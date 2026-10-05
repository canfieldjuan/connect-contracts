"""Offline ADR-0011 runtime conformance: shape and metadata only, not a model host."""

import copy
import json
import re
import unittest
from datetime import datetime
from itertools import product
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas/runtime/v1"
FIXTURES = ROOT / "fixtures/runtime/v1"
CANONICAL = ROOT / "runtime/v1/profile.json"

# ADR-0011 "Canonical profile": the exact argv. The CPU tier drops `--device <device>` and
# uses `-ngl 0 -t <physical cores>` in place of `-ngl 999 -fa on`.
THINKING_OFF = '{"enable_thinking":false}'
GPU_ARGV = [
    "-m", "<model>", "--device", "<device>", "-c", "32768", "-np", "1", "-ngl", "999",
    "-fa", "on", "--jinja", "--chat-template-kwargs", THINKING_OFF, "--reasoning", "off",
    "--alias", "<GGUF sha256>", "--api-key-file", "<key>", "--offline", "--no-webui",
    "--no-warmup", "--host", "<socket>",
]
CPU_ARGV = [
    "-m", "<model>", "-c", "32768", "-np", "1", "-ngl", "0", "-t", "<physical cores>",
    "--jinja", "--chat-template-kwargs", THINKING_OFF, "--reasoning", "off",
    "--alias", "<GGUF sha256>", "--api-key-file", "<key>", "--offline", "--no-webui",
    "--no-warmup", "--host", "<socket>",
]
TIER_ORDER = ["gpu-cuda", "gpu-vulkan", "cpu"]
DEVICE_CLASS = {"gpu-cuda": "nvidia-cuda", "gpu-vulkan": "vulkan-discrete", "cpu": "cpu"}
ARCHIVE_SUFFIXES = (".tar.gz", ".tar.xz")
SOCKET_SUFFIX = "/local-connect/model/v1/server.sock"
MAX_SOCKET_PATH_BYTES = 107  # sun_path is 108 bytes including the terminating NUL
MAX_LOG_TAIL_BYTES = 4096
HF_PATH = re.compile(r"^/[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*/resolve/[0-9a-f]{40}/[^/]+$")
GITHUB_PATH = re.compile(r"^/ggml-org/llama\.cpp/releases/download/b[0-9]+/[^/]+$")
NVIDIA_PATH = re.compile(r"^/compute/cuda/redist/[a-z_]+/linux-x86_64/[^/]+$")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def expected_argv(tier_id):
    return CPU_ARGV if tier_id == "cpu" else GPU_ARGV


def url_errors(where, pin, hosts):
    errors = []
    url = pin["url"]
    if any(ord(ch) < 0x21 or ord(ch) == 0x7F for ch in url):
        return [f"{where}: URL contains a control or space character"]
    parts = urlsplit(url)
    if parts.scheme != "https":
        errors.append(f"{where}: URL is not https")
    if parts.username or parts.password or parts.port or parts.query or parts.fragment:
        errors.append(f"{where}: URL carries credentials, a port, a query or a fragment")
    patterns = {
        "huggingface.co": HF_PATH,
        "github.com": GITHUB_PATH,
        "developer.download.nvidia.com": NVIDIA_PATH,
    }
    if parts.hostname not in hosts:
        errors.append(f"{where}: URL host {parts.hostname!r} is not one of {sorted(hosts)}")
    elif not patterns[parts.hostname].match(parts.path):
        errors.append(f"{where}: URL is not a pinned release or a fixed revision")
    if PurePosixPath(parts.path).name != pin["file_name"]:
        errors.append(f"{where}: URL does not end in the pinned file name")
    return errors


def path_errors(where, value):
    segments = value.split("/")
    if (
        value.startswith("/")
        or "\\" in value
        or any(segment in ("", ".", "..") for segment in segments)
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)
    ):
        return [f"{where}: path {value!r} is not a plain relative path inside the runtime set"]
    return []


def profile_semantic_errors(profile):
    errors = []
    ids = [tier["id"] for tier in profile["tiers"]]
    if len(set(ids)) != len(ids):
        errors.append("a tier appears twice")
    elif ids != [tier for tier in TIER_ORDER if tier in ids]:
        errors.append("tiers are not in preference order (gpu-cuda, gpu-vulkan, cpu)")
    models = {}
    for tier in profile["tiers"]:
        tid = tier["id"]
        if tier["device_class"] != DEVICE_CLASS[tid]:
            errors.append(f"{tid}: device class must be {DEVICE_CLASS[tid]}")
        req = tier["requirements"]
        has_cuda = "cuda_compute_capabilities" in req or "min_driver_cuda_version" in req
        if tid == "gpu-cuda" and not (
            "cuda_compute_capabilities" in req and "min_driver_cuda_version" in req
        ):
            errors.append("gpu-cuda: needs compute capabilities and a minimum driver CUDA version")
        if tid != "gpu-cuda" and has_cuda:
            errors.append(f"{tid}: CUDA requirements belong only to gpu-cuda")
        if (tid == "cpu") != ("cpu_features" in req):
            errors.append(f"{tid}: CPU features belong exactly to the cpu tier")
        if tier["argv"] != expected_argv(tid):
            errors.append(f"{tid}: argv differs from ADR-0011's canonical argv")

        model = tier["model"]
        if not model["file_name"].endswith(".gguf"):
            errors.append(f"{tid}: the model is not a .gguf file")
        errors.extend(url_errors(f"{tid} model", model, {"huggingface.co"}))
        previous = models.setdefault(model["sha256"], model)
        if previous != model:
            errors.append(f"{tid}: one model hash is pinned with two different file records")

        runtime = tier["runtime"]
        archive = runtime["archive"]
        if not archive["file_name"].endswith(ARCHIVE_SUFFIXES):
            errors.append(f"{tid}: the runtime archive is not .tar.gz or .tar.xz")
        errors.extend(url_errors(f"{tid} runtime", archive, {"huggingface.co", "github.com"}))
        paths = [entry["path"] for entry in runtime["files"]]
        for entry_path in paths:
            errors.extend(path_errors(f"{tid} files", entry_path))
        if len(set(paths)) != len(paths):
            errors.append(f"{tid}: a runtime file is listed twice")
        errors.extend(path_errors(f"{tid} server_path", runtime["server_path"]))
        if runtime["server_path"] not in paths:
            errors.append(f"{tid}: the server is not in the runtime set's file manifest")
        libraries = runtime.get("libraries")
        if (tid == "gpu-cuda") != (libraries is not None):
            errors.append(f"{tid}: NVIDIA library archives belong exactly to gpu-cuda")
        for library in libraries or []:
            lib = library["archive"]
            if not lib["file_name"].endswith(".tar.xz"):
                errors.append(f"{tid}: an NVIDIA library archive is not .tar.xz")
            errors.extend(url_errors(f"{tid} library", lib, {"developer.download.nvidia.com"}))
            for member in library["members"]:
                errors.extend(path_errors(f"{tid} member archive_path", member["archive_path"]))
                errors.extend(path_errors(f"{tid} member path", member["path"]))
                if member["path"] not in paths:
                    errors.append(f"{tid}: library member {member['path']!r} is not in the manifest")
    return errors


def timestamp_errors(where, value):
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [f"{where}: not a real UTC time"]
    return []


def server_semantic_errors(document):
    errors = timestamp_errors("ready_by", document["ready_by"])
    if document["state"] == "ready" and document["server"] is None:
        errors.append("a ready registration names its server")
    if document["tier"] is not None and (document["tier"] == "cpu") != (document["device"] is None):
        errors.append("a GPU tier names exactly one device, and the cpu tier none")
    if document["server"] is not None and document["server"]["pid"] == document["host"]["pid"]:
        errors.append("the server and the host are one process")
    socket = document["socket_path"]
    if not socket.startswith("/") or not socket.endswith(SOCKET_SUFFIX):
        errors.append(f"the socket path must be absolute and end with {SOCKET_SUFFIX}")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in socket) or "/../" in socket or "/./" in socket:
        errors.append("the socket path is not a plain absolute path")
    if len(socket.encode("utf-8")) > MAX_SOCKET_PATH_BYTES:
        errors.append(f"the socket path exceeds {MAX_SOCKET_PATH_BYTES} bytes")
    return errors


def failure_semantic_errors(document):
    errors = timestamp_errors("at", document["at"])
    lines = document["log_tail"]
    if any("\n" in line or "\r" in line for line in lines):
        errors.append("a log tail item is more than one line")
    if len("\n".join(lines).encode("utf-8")) > MAX_LOG_TAIL_BYTES:
        errors.append(f"the log tail exceeds {MAX_LOG_TAIL_BYTES} bytes")
    return errors


SEMANTIC = {
    "profile.schema.json": profile_semantic_errors,
    "server.schema.json": server_semantic_errors,
    "failure.schema.json": failure_semantic_errors,
}


def errors_for(schema_name, document):
    schema = load(SCHEMAS / schema_name)
    errors = [
        error.message
        for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)
    ]
    if not errors:
        errors.extend(SEMANTIC[schema_name](document))
    return errors


class RuntimeContractTests(unittest.TestCase):
    def test_schema_documents_are_valid(self):
        for name in SEMANTIC:
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(load(SCHEMAS / name))

    def test_fixture_inventory_is_complete(self):
        index = load(FIXTURES / "index.json")
        listed = {case["fixture"] for case in index}
        present = {str(path.relative_to(FIXTURES)) for path in FIXTURES.glob("*/*.json")}
        self.assertEqual(listed, present)
        self.assertEqual(len(index), len(listed))

    def test_fixtures_match_their_expected_validity(self):
        for case in load(FIXTURES / "index.json"):
            with self.subTest(fixture=case["fixture"]):
                errors = errors_for(case["schema"], load(FIXTURES / case["fixture"]))
                self.assertEqual(not errors, case["valid"], errors)

    def test_the_canonical_argv_is_adr_0011s(self):
        adr = (ROOT / "adr/0011-shared-local-model-runtime.md").read_text(encoding="utf-8")
        block = adr.split("```text\n-m <model>", 1)[1].split("```", 1)[0]
        # A placeholder may contain a space (`<GGUF sha256>`); the JSON kwarg has none.
        written = re.findall(r"<[^>]+>|\S+", "-m <model>" + block)
        self.assertEqual(written, GPU_ARGV)
        self.assertIn("`-ngl 0 -t <physical cores>` in place of\n`--device <device> -ngl 999 -fa on`", adr)
        cpu_from_gpu = GPU_ARGV[:2] + GPU_ARGV[4:8] + ["-ngl", "0", "-t", "<physical cores>"] + GPU_ARGV[12:]
        self.assertEqual(cpu_from_gpu, CPU_ARGV)

    def test_any_argv_change_is_refused(self):
        base = load(FIXTURES / "valid/profile-three-tiers.json")
        mutations = {
            "extra listener": lambda argv: argv + ["--port", "8080"],
            "network download": lambda argv: argv + ["-hf", "org/repo"],
            "inline key": lambda argv: argv[:19] + ["--api-key", "secret"] + argv[21:],
            "thinking on": lambda argv: [a.replace("false", "true") for a in argv],
            "context halved": lambda argv: [("16384" if a == "32768" else a) for a in argv],
            "reordered": lambda argv: argv[2:4] + argv[:2] + argv[4:],
            "flag dropped": lambda argv: [a for a in argv if a != "--no-warmup"],
            "placeholder filled": lambda argv: [("/tmp/m.gguf" if a == "<model>" else a) for a in argv],
        }
        for name, mutate in mutations.items():
            for index in range(3):
                with self.subTest(mutation=name, tier=base["tiers"][index]["id"]):
                    document = copy.deepcopy(base)
                    document["tiers"][index]["argv"] = mutate(document["tiers"][index]["argv"])
                    self.assertTrue(errors_for("profile.schema.json", document))

    def test_urls_must_be_pinned_https_releases(self):
        base = load(FIXTURES / "valid/profile-three-tiers.json")
        model_url = base["tiers"][0]["model"]["url"]
        cases = {
            model_url: True,
            model_url.replace("https://", "http://"): False,
            model_url.replace("0123456789abcdef0123456789abcdef01234567", "main"): False,
            model_url.replace("0123456789abcdef0123456789abcdef01234567", "0123456"): False,
            model_url + "?download=true": False,
            model_url.replace("huggingface.co", "huggingface.co:8443"): False,
            model_url.replace("huggingface.co", "user@huggingface.co"): False,
            model_url.replace("huggingface.co", "hf-mirror.example"): False,
            model_url.replace("fixture-9b.gguf", "other.gguf"): False,
            model_url + "#frag": False,
            model_url.replace("resolve", "resolve/x"): False,
        }
        for url, valid in cases.items():
            with self.subTest(url=url):
                document = copy.deepcopy(base)
                for tier in document["tiers"][:2]:
                    tier["model"]["url"] = url
                self.assertEqual(not errors_for("profile.schema.json", document), valid)

    def test_runtime_paths_stay_inside_the_set(self):
        base = load(FIXTURES / "valid/profile-three-tiers.json")
        for value, valid in (
            ("build/bin/libextra.so", True),
            ("libextra.so", True),
            ("/usr/lib/libextra.so", False),
            ("../libextra.so", False),
            ("build/../../libextra.so", False),
            ("build//libextra.so", False),
            ("build/./libextra.so", False),
            ("build\\libextra.so", False),
            ("build/lib\nextra.so", False),
            ("", False),
        ):
            with self.subTest(path=repr(value)):
                document = copy.deepcopy(base)
                document["tiers"][2]["runtime"]["files"].append({"path": value, "sha256": "b3" * 32})
                self.assertEqual(not errors_for("profile.schema.json", document), valid)

    def test_sizes_floors_and_hashes_reject_falsy_and_malformed_values(self):
        base = load(FIXTURES / "valid/profile-three-tiers.json")
        for value, valid in ((1, True), (5_627_044_256, True), (0, False), (-1, False),
                             (False, False), (True, False), ("", False), (None, False), (1.5, False)):
            with self.subTest(size=repr(value)):
                document = copy.deepcopy(base)
                document["tiers"][2]["model"]["size_bytes"] = value
                self.assertEqual(not errors_for("profile.schema.json", document), valid)
        for value, valid in ((1, True), (1_048_576, True), (0, False), (1_048_577, False), (False, False)):
            with self.subTest(floor=repr(value)):
                document = copy.deepcopy(base)
                document["tiers"][0]["requirements"]["memory_floor_mib"] = value
                self.assertEqual(not errors_for("profile.schema.json", document), valid)
        for value, valid in (("a" * 64, True), ("A" * 64, False), ("a" * 63, False),
                             ("a" * 65, False), ("g" * 64, False), ("", False)):
            with self.subTest(sha=value):
                document = copy.deepcopy(base)
                document["tiers"][1]["runtime"]["archive"]["sha256"] = value
                self.assertEqual(not errors_for("profile.schema.json", document), valid)

    def test_tier_shape_rules_hold_on_both_sides(self):
        base = load(FIXTURES / "valid/profile-three-tiers.json")
        cuda, vulkan, cpu = base["tiers"]
        cases = {
            "all three": ([cuda, vulkan, cpu], True),
            "cpu only": ([cpu], True),
            "cuda and cpu": ([cuda, cpu], True),
            "empty": ([], False),
            "duplicate": ([cuda, cuda], False),
            "out of order": ([vulkan, cuda], False),
            "vulkan with libraries": ([dict(vulkan, runtime=dict(vulkan["runtime"], libraries=cuda["runtime"]["libraries"]))], False),
            "vulkan with cuda requirements": ([dict(vulkan, requirements=cuda["requirements"])], False),
            "cpu without features": ([dict(cpu, requirements={"memory_floor_mib": 4882})], False),
            "cuda without driver version": ([dict(cuda, requirements={"memory_floor_mib": 7330, "cuda_compute_capabilities": ["8.6"]})], False),
            "wrong device class": ([dict(cpu, device_class="nvidia-cuda")], False),
            "one hash, two records": ([cuda, dict(vulkan, model=dict(vulkan["model"], size_bytes=1))], False),
        }
        for name, (tiers, valid) in cases.items():
            with self.subTest(case=name):
                document = copy.deepcopy(base)
                document["tiers"] = copy.deepcopy(tiers)
                self.assertEqual(not errors_for("profile.schema.json", document), valid)

    def test_socket_path_length_boundary(self):
        base = load(FIXTURES / "valid/server-ready.json")
        for length, valid in ((len(SOCKET_SUFFIX) + 2, True), (106, True), (107, True), (108, False), (200, False)):
            with self.subTest(length=length):
                document = copy.deepcopy(base)
                document["socket_path"] = "/" + "r" * (length - len(SOCKET_SUFFIX) - 1) + SOCKET_SUFFIX
                self.assertEqual(len(document["socket_path"].encode()), length)
                self.assertEqual(not errors_for("server.schema.json", document), valid)
        for value in ("relative/local-connect/model/v1/server.sock", "/run/user/1000/other.sock",
                      "/run/user/1000/../local-connect/model/v1/server.sock",
                      "/run/user/10\n00/local-connect/model/v1/server.sock"):
            with self.subTest(socket=repr(value)):
                document = copy.deepcopy(base)
                document["socket_path"] = value
                self.assertTrue(errors_for("server.schema.json", document))

    def test_registration_states_and_identities(self):
        ready = load(FIXTURES / "valid/server-ready.json")
        cases = {
            "starting without server": (dict(ready, state="starting", server=None), True),
            "stopping without server": (dict(ready, state="stopping", server=None), True),
            "ready without server": (dict(ready, server=None), False),
            "unknown state": (dict(ready, state="running"), False),
            "cpu with device": (dict(ready, tier="cpu"), False),
            "gpu without device": (dict(ready, device=None), False),
            "gpu with empty device": (dict(ready, device=""), False),
            "server is host": (dict(ready, server={"pid": ready["host"]["pid"], "start_time": 1}), False),
            "pid zero": (dict(ready, host=dict(ready["host"], pid=0)), False),
            "pid boolean": (dict(ready, host=dict(ready["host"], pid=True)), False),
            "start id not v4": (dict(ready, start_id="3f2b8c1e-5d4a-1c3b-9a2f-1e0d9c8b7a65"), False),
            "ready_by not a date": (dict(ready, ready_by="2026-13-40T25:61:00Z"), False),
            "ready_by with offset": (dict(ready, ready_by="2026-09-27T23:05:00+01:00"), False),
            "context 16k": (dict(ready, context_tokens=16384), False),
            "extra field": (dict(ready, port=18081), False),
        }
        for name, (document, valid) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(not errors_for("server.schema.json", document), valid)

    def test_starting_before_profile_admission(self):
        selected = load(FIXTURES / "valid/server-starting.json")
        selection_keys = ("tier", "model_sha256", "context_tokens", "build_commit",
                          "chat_template_sha256")
        pending = dict(selected, device=None, server=None,
                       **{key: None for key in selection_keys})
        validator = Draft202012Validator(load(SCHEMAS / "server.schema.json"))
        self.assertEqual(list(validator.iter_errors(pending)), [])
        self.assertEqual(errors_for("server.schema.json", pending), [])
        for mask in product((False, True), repeat=len(selection_keys)):
            document = dict(pending)
            for key, known in zip(selection_keys, mask):
                if known:
                    document[key] = selected[key]
            if all(mask):
                document["device"] = selected["device"]
            valid = not any(mask) or all(mask)
            with self.subTest(selection=mask):
                self.assertEqual(validator.is_valid(document), valid)
                self.assertEqual(not errors_for("server.schema.json", document), valid)
        for state in ("ready", "stopping", "", None, False):
            with self.subTest(state=state):
                self.assertFalse(validator.is_valid(dict(pending, state=state)))
        for key in selection_keys + ("device", "server"):
            for value in ("", False, 0):
                with self.subTest(key=key, value=value):
                    self.assertFalse(validator.is_valid(dict(pending, **{key: value})))
            missing = dict(pending)
            del missing[key]
            with self.subTest(missing=key):
                self.assertFalse(validator.is_valid(missing))
        self.assertFalse(validator.is_valid(dict(pending, device="CUDA0")))
        self.assertFalse(validator.is_valid(dict(pending, server={"pid": 4243, "start_time": 2})))

    def test_failure_log_tail_boundaries(self):
        base = load(FIXTURES / "valid/failure-server-failed.json")
        for lines, valid in ((0, True), (1, True), (20, True), (21, False)):
            with self.subTest(lines=lines):
                self.assertEqual(not errors_for("failure.schema.json", dict(base, log_tail=["x"] * lines)), valid)
        for total, valid in ((4095, True), (4096, True), (4097, False)):
            with self.subTest(bytes=total):
                # two lines joined by one newline
                first = "a" * 2000
                second = "b" * (total - len(first) - 1)
                self.assertEqual(
                    not errors_for("failure.schema.json", dict(base, log_tail=[first, second])), valid
                )
        self.assertTrue(errors_for("failure.schema.json", dict(base, log_tail=["one\ntwo"])))
        for code in ("PROFILE_INVALID", "RUNTIME_FILES_INVALID", "STORE_UNSUPPORTED", "NO_TIER",
                     "GPU_BUSY", "SERVER_FAILED"):
            with self.subTest(code=code):
                self.assertFalse(errors_for("failure.schema.json", dict(base, code=code)))
        self.assertTrue(errors_for("failure.schema.json", dict(base, code="")))

    def test_the_canonical_profile_is_valid(self):
        if not CANONICAL.exists():
            self.skipTest(
                "runtime/v1/profile.json lands once its tiers qualify on the canonical argv "
                "(MODEL-SETUP MS-PIN-4)"
            )
        self.assertEqual(errors_for("profile.schema.json", load(CANONICAL)), [])


if __name__ == "__main__":
    unittest.main()
