# PluralKit feed mapping (proof of concept)

This maps `templates/model-feed-single.txt` through `gen-import-engine.py` into one native PluralKit version-2 export. It is a proof of concept. The shape is the owner export from commit `22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc`, described in `docs/pluralkit/pluralkit-record-reference.md`. It is not an API response. The comprehensive sample and that reference are unchanged. No official JSON Schema is applied.

```text
python gen-import-engine.py --model pluralkit --scriptfspec templates/model-feed-single.txt
```

JSON is `out/imports/pluralkit/<feed-stem>.json`. PNGs are `out/imports/pluralkit/<feed-stem>-avatars/<member short id>.png`. A failed run replaces neither that JSON nor that avatar directory.

## What the specimen becomes

| Feed | Export |
| --- | --- |
| System The Harbor | Root `name`. Profile fields sit beside `version`. |
| 53 ordinary members | `members`, once each. Range members are named `L<line>:<number>`. |
| Theatre | One group. Members are the 50 generated members, then Gilligan. |
| Backstage | One group. Its only member is Penny. |
| Popeye and Penny `front: true` | One switch at `2026-01-01T00:00:00Z` whose `members` are both short ids, Popeye then Penny. |
| Blurry `front: false` | Not a member and not in the switch. |
| Linked Discord accounts | `accounts` is `[]`. The feed has none. |

`version` is the number `2`. Group and switch arrays store member short ids. Member and group objects have no `system` key. Switches have no UUID. `webhook_url` is null.

## Identifiers and defaults

Short ids are five lowercase letters from SHA-256 of `system:`, `member:`, or `group:` plus the shared identity key. A collision uses the next salt. UUIDs are version 4 from SHA-256 of a `pluralkit:` key. `created` and the switch `timestamp` are `2026-01-01T00:00:00Z`.

The feed does not supply these exported fields. This cut writes:

| Field | Synthetic value |
| --- | --- |
| System `description`, `tag`, `pronouns`, `color` | JSON `null` |
| `avatar_url`, `banner`, `webhook_url` on the system | JSON `null` |
| Member `display_name`, `birthday`, `pronouns`, `description` | JSON `null` |
| Member `webhook_avatar_url`, `banner`, `avatar_url` | JSON `null` |
| Member `keep_proxy`, `tts`, `autoproxy_enabled` | `false` |
| Member `message_count` | `0` |
| Member `last_message_timestamp` | JSON `null` |
| Member `proxy_tags`, `aliases` | `[]` |
| Member `color` | The feed avatar color without `#`, lowercased, or null |
| Group `display_name`, `description`, `icon`, `banner`, `color` | JSON `null` |
| `config.timezone` | `UTC` |
| `config.member_limit`, `config.group_limit` | `1000` and `250` |
| `config.name_format` | `{name} {tag}` |
| `config.latch_timeout` | JSON `null` |
| `config.hid_list_padding` | `off` |
| `config.proxy_switch` | `off` |
| Other config booleans | `false` |
| `config.description_templates` | `[]` |
| `config.member_default_private`, `config.group_default_private` | `true` |

`1000`, `250`, `UTC`, and `{name} {tag}` are the defaults named in PluralKit's API settings table. The booleans and the null latch timeout are synthetic for this cut. They are not a claim about PluralKit's database defaults.

## Privacy

PluralKit privacy is only `public` or `private`. Every privacy key on the system, each member, and each group is `private`.

Account visibility `self` is that private value. Popeye's `trusted friends` is also `private`, which is narrower than trusted friends. Operation permission `read` is not a privacy value and not a role.

## Avatars

Resolved requests still go through `gen-avatars.py`. Popeye is 64×64 solid `#4a90e2`. Penny is 64×64 crosshatch `#ff8800`. The file name is the member short id plus `.png`.

Native `avatar_url` fields stay null. A local path or a data URI would not be a hosted URL, so this cut does not invent one. The PNG is a sidecar. Nothing in the JSON points at it.

## Unsupported supplied data

The export does not gain keys for data the native file cannot store. The run prints a `notice:` line for each of these:

- Account name and email.
- Account permission `read`.
- Account visibility `self` exported as private.
- Popeye's `trusted friends` narrowed to private.
- Backstage nested under Theatre.
- Notes `id1`, `id2`, and `id3`.
- Custom fields `title` and `author`, and Popeye's values `Sailor` and `Popeye`.
- Privacy bucket Close Friends, friend Alex, and Popeye's bucket assignment.
- Custom front Blurry.
- Gilligan's archived flag and reason.
- The two sidecar images having no hosted URL.

A Place or a second System is an error and does not replace an existing file.
