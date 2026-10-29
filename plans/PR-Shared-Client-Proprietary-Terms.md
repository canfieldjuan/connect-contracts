# U1 client: proposed proprietary source and build permissions

Status: PROPOSAL FOR REVIEW, not an operative license or permission to publish.
Owner: connect-runtime. Parent: [accepted U1 contract](PR-Shared-Runtime-U1.md).
This document proposes the missing licensing decision; it does not expand U1's
symbol/asset allowlist, replace third-party terms, or grant rights in private apps.
No LICENSE file, public repository, release, visibility change or app EULA is
created by this documentation PR. Juan identified the licensor/copyright owner as
Juan Canfield; copyright years and source-specific rights remain to be verified.
The wording requires legal/rights review and Juan's exact-revision acceptance;
technical oversight is not legal clearance or assurance of enforceability.

## Decision, root cause and required surface

Juan directly specified temporary public app visibility for CI and private
shipping apps, runtime, addons and automations. His coordinating-chat messages
were inspected at their source: "private licence they will need to pay to use
the apps" and "Public client source, proprietary terms". The small shared client
is the public-source exception. Public visibility does not select an open-source
license, and client build permissions do not confer paid app-use rights. Juan
also directly answered the owner-name question: "owner would be Juan Canfield".
This records his designation, not independent proof of every source right.

U1 requires anonymous source retrieval, clean CI builds and exact vendoring;
repository visibility alone does not specify the necessary permissions. The
candidate currently has no license declaration. The proposed repair is one
client-specific permission document plus accurate third-party notices, carried
unchanged in every client source archive and vendor copy. App commercial terms
remain separately owned. No technical source changes are part of this PR.

## Verified inventory and limits

- Host PR9 merged as `2969b25f3cf58c092873c7ca42e018ff0b3a5117`, reviewed
  `e25bd27e992f65fef90931777edbe688c9d011c0`; the trees match. The real
  [pull-request CI run](https://github.com/canfieldjuan/local-connect-model-host/actions/runs/40947961902)
  passed. This proves the private extraction checks, not public licensing/build
  readiness. No runtime/model inference measurement belongs to this proposal.
- Canonical local candidate `168c8d042911bee2531c1fadeb6fff12161d1cdb`,
  `crates/model-primitives/`, contains only U1a file primitives. Its
  `PROVENANCE.json` identifies original host `src/files.rs` at
  `f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b` and each extracted symbol/hash.
- The host's [source provenance](https://github.com/canfieldjuan/local-connect-model-host/blob/2969b25f3cf58c092873c7ca42e018ff0b3a5117/docs/SOURCE-PROVENANCE.md)
  traces earlier work to Document Summarizer
  `a19639a4133c85060f67aaf1042732555256f8b5`,
  `src-tauri/src/pipeline/llama_cpp.rs`. The pinned tree has no top-level
  LICENSE/COPYING/NOTICE file. Authorship and Git access are not proof of
  copyright ownership or sufficient permission to relicense all contributions.
- Offline locked Cargo metadata lists 28 packages including the unlicensed local
  candidate. Registry declarations mostly offer MIT and/or Apache-2.0;
  `unicode-ident 1.0.26` additionally requires Unicode-3.0, while
  `version_check 0.9.5` uses the legacy `MIT/Apache-2.0` expression. `r-efi 6.0.0`
  declares MIT OR Apache-2.0 OR LGPL-2.1-or-later; its permission and attribution
  text is in `AUTHORS`, not a LICENSE-named file. These are observed declarations,
  not a completed compatibility or ownership opinion.
- Durable inventory alias `proprietary-client-proposal-20261029/dependency-license-inventory.json`,
  SHA-256 `1739d184f632b471d13042030324f6013e84f6d02315236a8f3edfb3359413ee`,
  records versions, declarations and notice-file hashes. It covers this candidate
  only. Later profile/assets, lease, identity, client transport, Python and all
  release target/build/dev graphs require their own refreshed closure review.

## Permission matrix proposed for acceptance

"Publisher" below means the confirmed licensor and its expressly authorized
integrators/distributors. Anonymous means no private repository credential or
paid app entitlement is required for the client activity.

| Activity | Anyone, anonymously | Publisher | Boundary |
|---|---|---|---|
| Read, download, clone client source | Allowed | Allowed | Retain notice; no ownership transfer. |
| Public GitHub forks and platform collaboration | GitHub's applicable platform permissions remain intact | Allowed | Do not promise to prevent forks or erase prior public copies. |
| Build/test unmodified client in local or hosted CI | Allowed | Allowed | Client build/test permission requires no paid account; app source has separate terms. |
| Modify client privately for evaluation, security analysis or proposed fixes; submit patches | Allowed | Allowed | Mark modifications; no automatic right to distribute a modified product or operate a hosted service. |
| Test patches in public contribution forks/CI | Allowed for contribution review | Allowed | Public patches and client test artifacts may support review, not a substitute production distribution channel. |
| Vendor exact client release into designated product build/CI checkouts | Allowed for development/test copies | Allowed for development and releases | Preserve full source closure, manifest, provenance and notices; no app-source permission is implied. |
| Redistribute client-containing official app/host releases | Separate written authorization required | Allowed within that authorization | Same immutable client bytes; preserve third-party notices; customer app terms remain separate. |
| Publish official standalone client source archives | Separate written authorization required | Allowed | Public archive access is necessary for U1; no public host or app source bundled. |
| Redistribute a modified client or embed it in unrelated products/services | Separate written permission required | Only with expressly approved scope | GitHub platform and third-party rights are not narrowed by this row. |
| Use paid apps for ordinary business work | Governed by separate app license | Governed by separate app terms | Client access/build rights do not supply an entitlement or authorize bypassing checks. |

### External designated-products record

One licensor-maintained, versioned record owns product designations outside the
client release. Proposed stable location:
`https://github.com/canfieldjuan/connect-contracts/blob/main/records/shared-client-designated-products.json`.
This is a reserved location to establish before adopting the terms, not a claim
that a record exists there today. The record is not part of the client archive,
vendored source tree or its file manifest. Terms refer to this stable location;
adding a product changes only the record and that consumer's permission receipt,
not the client terms, release hash or existing consumers' client identity.

The record must retain immutable revisions, a schema version, stable product IDs,
licensor approval and effective dates, and the applicable terms/client release
scope for each designation. A consumer records the exact record revision/hash
and relevant entry alongside its qualification evidence. This is permission
provenance, not a runtime lookup or new app admission policy. Keep prior revisions
available; additions do not revoke existing designations or force other consumers
to requalify unchanged client bytes. Withdrawal or changed permissions require
separate reviewed terms and authority; silently editing history is not allowed.

Proposed initial entries: Document Summarizer, Email Watcher, Invoice Processor,
and the Local Connect shared model host. These entries still require acceptance;
this proposal does not create an operative designation. Future addons,
automations and other products, including Connect Automate packs, require Juan's
express designation. Product designation does not itself authorize production
distribution, expose private source or replace separate publisher authorization.
Private shipping apps can still consume the exact client archive.

## Proposed notice and terms — draft only

The following is proposed text for a future client `LICENSE` plus referenced
third-party notices. It has no effect while embedded in this proposal.

> **Local Connect Shared Client — Proprietary Source and Build Terms, draft v1**
>
> Copyright [VERIFIED YEARS] Juan Canfield (the Licensor). Rights are reserved except
> for the permissions expressly stated here or granted under separate terms.
>
> **1. Scope.** These terms cover only the licensor-controlled portions of the
> shared client and primitives identified by the accompanying source manifest
> (the Client). They do not license application source, application use, model
> weights, the inference engine, private host implementation, trademarks or
> other products. Third-party materials remain subject to their own terms and
> notices. These terms do not restrict rights granted directly by third parties,
> applicable law or GitHub's applicable platform terms.
>
> **2. Inspection and development.** The Licensor grants you a nonexclusive,
> worldwide, royalty-free permission to read, download, clone and make copies
> of the Client; compile it; run its tests; and modify it for private evaluation,
> security analysis and preparation of contributions. You may perform these
> activities in local or hosted automated build systems without a paid app
> account or a private-source credential. You may share proposed patches in
> contribution forks and pull requests and run public CI for their review.
> Preserve these terms and applicable notices and identify your modifications.
>
> **3. Designated-product builds.** You may vendor the complete, unmodified,
> hash-identified Client release in development or CI copies of the designated
> products in the Licensor's versioned designated-products record at
> https://github.com/canfieldjuan/connect-contracts/blob/main/records/shared-client-designated-products.json,
> and compile/test those integrations to the extent you independently have
> permission to use their source. The record is maintained separately from this
> Client release. Retain the applicable record revision and designation as
> permission evidence; adding a product does not alter this release or its terms.
> Build caches,
> logs and Client test artifacts may be retained or shared as necessary for
> development and review, including public CI. This permission does not authorize
> publishing product source or distributing production app/host binaries.
>
> **4. Authorized distribution.** The Licensor and persons expressly authorized
> in writing for the relevant product may publish official Client source
> archives, vendor the complete unmodified release in designated product source
> distributions, and distribute Client binaries incorporated in those products.
> Recipients retain the Client permissions stated here. Preserve notices,
> provenance and the pinned source manifest; do not present a changed copy as
> the reviewed release. Other standalone redistribution, distribution of modified
> Client versions, unrelated-product integration and hosted-service operation
> require separate written permission, except for independently granted rights
> preserved by section 1. Public CI is not a production distribution workaround.
>
> **5. Paid applications.** A separately issued application license governs
> ordinary use of each paid application. Client source access, compilation,
> testing, possession of a binary or a GitHub fork does not grant that license.
> While authorized under that application's license, you may execute the Client
> supplied with it, including its shared-host integration, solely to support that
> authorized use, without an additional Client royalty. Development/test rights
> in sections 2–3 do not require that application entitlement.
> These terms do not authorize circumventing app entitlement controls. They do
> not set pricing, seats, subscriptions, offline entitlement or support rights.
>
> **6. Contributions and rights.** Submit only contributions you are entitled
> to submit, with applicable attribution. A contribution offered for incorporation
> is offered under these Client terms; no copyright assignment is implied.
> The publisher must separately verify any rights needed to incorporate or
> commercially distribute contributed work. These terms grant no rights to
> third-party code beyond those its own licensors grant.
>
> **7. Versions and visibility.** Each released copy identifies its terms version
> and preserves its notices. Changing repository visibility or releasing new
> terms does not purport to recall copies already obtained or retroactively
> replace the terms accompanying them. No trademark or endorsement permission
> is granted by these terms.
>
> **8. No assurance.** To the extent permitted by applicable law, the Client is
> supplied without warranties or a support/service commitment. Mandatory legal
> rights and obligations are unaffected. Final warranty, liability, termination
> and dispute provisions require legal review before these terms take effect.

The last sentence explicitly leaves completion work; do not publish the draft
as a finished commercial agreement. Do not insert an open-source SPDX identifier
for these custom terms. A future Cargo `license-file` must point to the reviewed
operative text; the approved manifest includes it and the third-party notice set.

## Authoritative constraints and rights checks

GitHub's [Terms of Service D.3–D.6](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#d-user-generated-content)
reserve platform permissions for public content and require uploaders to have
the necessary rights. The [corporate terms](https://docs.github.com/en/site-policy/github-terms/github-corporate-terms-of-service)
also describe public viewing/forking permissions. Verify which agreement governs
the publishing account. This proposal cannot promise public source without
those platform permissions. [Existing public forks remain public](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)
when the original repository becomes private; privacy at shipping is not a
retroactive source-recall mechanism.

GitHub distinguishes [source visibility from repository licensing](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
Whether this custom grant is sufficient for every planned CI/distribution act
requires review. Public CI availability is not a licensing conclusion or a
guarantee of unlimited/uninterrupted CI service.

Proposed dependency treatment: select and document the MIT alternative where
the actual upstream grant offers it, retaining exact copyright/permission text;
retain additional mandatory notices such as Unicode-3.0. The
[MIT text](https://opensource.org/license/mit) requires preservation of its notice;
[Unicode's text](https://www.unicode.org/license.txt) also specifies attribution
conditions. Use the actual pinned notices rather than replacing them with newer
copyright years. Resolve the legacy expression and full `AUTHORS` grants from
the package contents before approving selections. No LGPL obligation is inferred
merely because LGPL appears as an alternative; no alternative is selected solely
by a substring scan either. Private host/model/engine distribution has separate
third-party obligations and is not cleared by a client license review.

## Concrete operator decisions and publication gates

1. Recorded owner designation: Juan Canfield, from his direct answer. Verify
   copyright years and employee, contractor and contributor authority for each
   extracted source origin. The named owner does not alone prove those rights.
2. Review the proposed permission matrix and text as a whole: free anonymous
   client development/CI, restricted production distribution, and separate paid
   app rights. No additional broad "public or private" choice is needed.
3. Resolve contribution/commercial distribution authority and complete legal
   wording, including applicable warranty/liability/termination provisions.
   Record approved publishers separately; establish the external designated-products
   record at the stable location above, validate its revision/history rules and
   obtain Juan's acceptance of its initial entries. Do not infer designation or
   distribution authority from repository write access or a PR approval.
4. Verify the exact full release's third-party/asset closure and notice bundle,
   then obtain independent review and Juan's exact-revision acceptance of the
   final terms. The current partial candidate inventory is not that full review.
5. Only afterward install operative LICENSE/NOTICE files in canonical source,
   regenerate hashes/vendor copies, and qualify the accepted anonymous public
   release/CI path. Public repository/release creation remains a separately
   authorized action. Shipping app entitlement and privacy gates remain separate.

## Verification, implementation summary and cold diff

Documentation only. Reused U1 symbol/provenance inventory and inspected pinned
dependency declarations/notices; did not re-run model/application benchmarks.
Check relative links and source bindings, proposal-status markers, unresolved
copyright-year field, no implied app/model/host grant, full permission-matrix coverage
and unchanged source allowlist. No code tests are appropriate for this proposal.
This proposal owns the matrix, draft wording, external-record mechanism and review
gates. The parent add-an-app checklist references that mechanism; it does not
duplicate product entries. No active license or designation record is introduced.

Review gap G1 originated in this proposal at `2b42e04`: section 3 enumerated
products and section 4 referred to products "listed with these terms". Extending
that list inside a hashed release would change its identity. The proposed origin
fix replaces that coupling with one external record and adds the missing parent
checklist step. Boundary check: an approved added product changes the external
record/consumer receipt only; an undesignated product gains no permission from
repository access. Existing client bytes, allowlists and transport stay unchanged.
The previous in-release designation mechanism is removed, not supplemented.

## Gap audit

NOT DONE: this is a concrete licensing proposal, not an adopted license or public
release. Source rights/years, external record and initial designations, final legal
wording, full third-party clearance,
independent review, exact-revision acceptance and publication authorization remain.
