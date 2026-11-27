# PluralPort feed mapping (proof of concept)

This maps `templates/model-feed-single.txt` through `gen-import-engine.py` into one OpenPlural 0.1 file. It is a proof of concept. The captured specification in `PP/pluralport.zip` includes no official JSON Schema, and this output is not claimed to pass one. `docs/pluralport/pluralport-comprehensive-example.json` and `docs/pluralport/pluralport-record-reference.md` are unchanged reference artifacts.

```text
python gen-import-engine.py --model pluralport --scriptfspec templates/model-feed-single.txt
```

The file is `out/imports/pluralport/<feed-stem>.json`. A failed run does not replace that file and does not clear other targets.

## Supported scope

One top-level System and Groups inside it. Ordinary members, one custom front, group membership, text custom fields and member values, member-owned notes, open front periods, and inline avatar assets. A Place, a second or nested System, an anchor relationship, a Group custom-field association, or a note with no member is an error.

Chat, boards, relationships, taxonomy, and the sketched sharing module are not written. They are not declared in `capabilities.modules`.

## Defaults

| Output | Value |
| --- | --- |
| `openplural_version` | `"0.1"` |
| `exported_at`, `created_at`, and `started_at` | `2026-01-01T00:00:00Z` |
| Producer `app` | `plural-synthetic`. `app_id` is omitted. That name is not a registered app id, and the producer is not Lighthouse. |
| File-local `id` | UUID version 4 from SHA-256 of a stable key. The version nibble is 4 and the variant is RFC 4122. |
| System `name` | The System anchor name. Account name and email are not copied onto that field. |
| Range member `name` | `L<line>:<number>` from the member-range declaration. |
| Custom field `field_type` | `text`. `supports_markdown` is `false`. |
| Note `title` | JSON `null`. The body is the quoted feed text. |
| Open front `ended_at` | JSON `null`. One assignment, `front_role` `member`. `source_kind` is `unknown` because the feed supplies a boolean, not an event pair. |
| Custom front `front:false` | A Member with `is_custom_front` true and no front period. |
| `source_refs` | Omitted. `plural-synthetic` is not a registered source app id. Feed script ids that are not already the record name are kept under the extension. |

## Privacy

`privacy.visibility` uses the specification’s closed set. `privacy.source` keeps the feed token.

| Feed audience | `visibility` |
| --- | --- |
| omitted, `self`, `only you`, `inherit` | `private` |
| `trusted friends` | `trusted` |
| `all friends` | `friends` |
| `selected people` | `unknown` |

`privacy.source.feed_visibility` is the original token. `resolved_from` is `account` or `member`. Account `Permission` is not copied into visibility or into a role.

## Extension `org.thepluralbridge`

Written on the envelope:

| Field | Contents |
| --- | --- |
| `account.name`, `account.email`, `account.permission`, `account.visibility` | Account settings from the feed. |
| `system_script_id` | The System anchor’s script id, when it has one. |
| `privacy_buckets` | `{script_id, name}` for each bucket. The name is not treated as an access rule. |
| `friends` | `{script_id, name, trusted, bucket_script_ids}`. A friend is not a Member. |
| `member_buckets` | `{member_id, member_name, bucket_script_ids}` for members the feed assigns to a bucket. `member_id` is the file-local Member id. |

A member `archivedReason` is `extensions.org.thepluralbridge.archived_reason` on that Member. `archived` itself is the core boolean. Group, field, note, and custom-front script ids are the same extension object’s `script_id` on those records.

## Warnings

Envelope `warnings` use `level` `warning`. They name data that exists only in the extension:

- `account_preserved_in_extension`
- `permission_not_mapped`
- `sharing_preserved_in_extension` when buckets, friends, or member bucket assignments exist
- `archive_reason_preserved_in_extension` for each archive reason

## Avatars

Resolved requests are drawn with `gen-avatars.py`. Each generated image is an Asset with `kind` `avatar`, `mime_type` `image/png`, `data_base64`, `size_bytes`, `sha256`, `width`, and `height`. `uri` and `data_uri` are null. The Member `avatar_asset_id` points at that asset. `file_name` is `<member name>.png`. Members with avatar `none` have no asset.
