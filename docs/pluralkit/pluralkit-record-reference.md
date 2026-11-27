# PluralKit sample export and record reference

This note describes `docs/pluralkit/pluralkit-comprehensive-example.json`. The sample is fictional. It follows the native export built by `ExportSystem` at the commit below. It is not an API response, and it is not claimed to be accepted unchanged on import.

No JSON Schema for this export was found in the inspected repository. Nothing here is official schema validation.

## Source

| Item | Value |
| --- | --- |
| Repository | https://github.com/PluralKit/PluralKit |
| Commit | `22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc` |
| Commit date | 2026-11-12T01:09:34Z |
| Export entry | [`DataFileService.ExportSystem`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Services/DataFileService.cs) |
| Published API models | [`docs/content/api/models.md`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/docs/content/api/models.md), also published at https://pluralkit.me/api/models/ |

`ExportSystem` calls `PKSystem.ToJson(LookupContext.ByOwner)` and merges that object into the root. It then adds `config`, `accounts`, `members`, `groups`, and `switches`. Member and group serializers are called with `LookupContext.ByOwner`. Groups are called with `needsMembersArray: true`. Member and group calls do not pass a system id string.

Words used here:

- **Always emitted** means this export path calls `JObject.Add` for the key on every record of that kind.
- **Omitted** means this path does not add the key. That is different from JSON `null`.
- **Source rule** means a check or enum in the inspected C# code.
- **API documentation** means `docs/content/api/models.md` at this commit. Those notes are not the export serializer.
- **Import observation** means a field the export writes and a `FromJSON` / `FromJson` method on this commit does not read. It is not a complete import specification.

## Root export

One system file. `version` is the JSON number `2`, then the system profile fields, then the collections.

| Item | Value |
| --- | --- |
| Purpose | Owner export of one system. |
| JSON path | `$` |
| Serializer | `DataFileService.ExportSystem`, merging `PKSystemExt.ToJson` |

```json
{
  "version": 2,
  "id": "aaaaa",
  "config": {},
  "accounts": [],
  "members": [],
  "groups": [],
  "switches": []
}
```

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `version` | number | Export version literal `2`. | Always emitted. Not a string. | Source rule: `o.Add("version", 2)`. |
| `id` | string | System short id. | Always emitted by the system serializer. | See System profile. |
| `uuid` | string | System UUID. | Always emitted. | See Identifiers. |
| `name` | string or null | System name. | Always emitted. Null when unset. | API docs: 100-character limit. |
| `description` | string or null | System description. | Always emitted. | API docs: 1000-character limit. |
| `tag` | string or null | Proxy tag suffix text. | Always emitted. | API docs: 79-character limit (`Limits.MaxSystemTagLength` is 79). |
| `pronouns` | string or null | System pronouns. | Always emitted. | API docs: 100-character limit. |
| `avatar_url` | string or null | System avatar URL after CDN cleanup. | Always emitted. | See Images. |
| `banner` | string or null | System banner URL after CDN cleanup. | Always emitted. | See Images. |
| `color` | string or null | Stored color. | Always emitted. | See Colors. |
| `created` | string | System creation time. | Always emitted. | See Timestamps. |
| `webhook_url` | string or null | Legacy webhook URL. | Always emitted for an owner export. The sample uses null. | Import observation: `SystemPatch.FromJSON` does not read `webhook_url`. `webhook_token` is commented out in `ToJson` and is not exported. |
| `privacy` | object | System privacy. | Always an object for `LookupContext.ByOwner`. A non-owner call would emit JSON `null` instead. | See System privacy. |
| `config` | object | System configuration. | Always emitted, including when the system has no groups. | See System configuration. |
| `accounts` | array of numbers | Linked Discord account ids. | Always emitted. Empty when none are linked. | `GetSystemAccounts` returns `IEnumerable<ulong>`. See Linked accounts. |
| `members` | array of objects | Members. | Always emitted. Empty when the system has none. | Order is not specified. `GetSystemMembers` has no `ORDER BY`. |
| `groups` | array of objects | Groups, each with a `members` array. | Always emitted. | Order is not specified. |
| `switches` | array of objects | Exported switches. | Always emitted. | Newest first in the current query. See Switch records. |

`ExportSystem` does not add a `system` wrapper. System profile fields sit beside `version`.

## System profile

| Item | Value |
| --- | --- |
| Purpose | The system fields merged into the root. |
| JSON path | `$` |
| Serializer | [`PKSystemExt.ToJson`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Models/PKSystem.cs) |

The sample root is the full object. Profile fields that can be null are still present: the sample sets `webhook_url` to null and gives the other profile strings values. A stored null name, description, tag, pronouns, avatar, banner, or color is still that key with JSON `null`.

`NameFor` and `DescriptionFor` hide values only when privacy denies access. This export uses `ByOwner`, and `PrivacyLevel.CanAccess` is true for the owner even when the level is `private`. The sample therefore contains the stored strings, not redacted replacements.

## System privacy

| Item | Value |
| --- | --- |
| Purpose | Per-field visibility stored for the system. |
| JSON path | `$.privacy` |
| Serializer | `PKSystemExt.ToJson` |

```json
{
  "name_privacy": "public",
  "avatar_privacy": "public",
  "description_privacy": "private",
  "banner_privacy": "public",
  "pronoun_privacy": "public",
  "member_list_privacy": "public",
  "group_list_privacy": "private",
  "front_privacy": "private",
  "front_history_privacy": "private"
}
```

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `name_privacy` | string | Name visibility. | Always emitted inside the object. | Source rule: `public` or `private` only. |
| `avatar_privacy` | string | Avatar visibility. | Always emitted. | Same enum. |
| `description_privacy` | string | Description visibility. | Always emitted. | Same enum. |
| `banner_privacy` | string | Banner visibility. | Always emitted. | Same enum. |
| `pronoun_privacy` | string | Pronoun visibility. | Always emitted. | Same enum. |
| `member_list_privacy` | string | Member-list visibility. | Always emitted. | Same enum. |
| `group_list_privacy` | string | Group-list visibility. | Always emitted. | Same enum. |
| `front_privacy` | string | Current-front visibility. | Always emitted. | Same enum. |
| `front_history_privacy` | string | Front-history visibility. | Always emitted. | Same enum. |

[`PrivacyLevel`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Models/Privacy/PrivacyLevel.cs) is `Public = 1` and `Private = 2`. `ToJsonString` returns `public` or `private`. There is no friends, trusted, or bucket value.

`public` and `private` cannot both be stored in one of these fields. The sample uses each value on at least one field.

## System configuration

| Item | Value |
| --- | --- |
| Purpose | System settings included in the owner export. |
| JSON path | `$.config` |
| Serializer | [`SystemConfigExt.ToJson`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Models/SystemConfig.cs) |

```json
{
  "timezone": "UTC",
  "pings_enabled": true,
  "latch_timeout": null,
  "member_default_private": true,
  "group_default_private": false,
  "show_private_info": true,
  "member_limit": 1000,
  "group_limit": 250,
  "case_sensitive_proxy_tags": false,
  "proxy_error_message_enabled": true,
  "hid_display_split": false,
  "hid_display_caps": false,
  "hid_list_padding": "off",
  "card_show_color_hex": false,
  "proxy_switch": "new",
  "name_format": "{name} {tag}",
  "description_templates": ["A synthetic description template."]
}
```

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `timezone` | string | `SystemConfig.UiTz`. | Always emitted. | API docs say the default is `UTC`. `SystemConfigPatch` rejects a timezone `DateTimeZoneProviders.Tzdb` does not know. |
| `pings_enabled` | boolean | Whether the bell reaction can ping. | Always emitted. | |
| `latch_timeout` | number or null | Latch timeout in seconds. | Always emitted. Null in the sample. | API docs: null means 6 hours, `0` means never. Null, `0`, and a positive number cannot coexist. |
| `member_default_private` | boolean | Default privacy for members created by the bot. | Always emitted. | API docs: this does not apply to API-created members. |
| `group_default_private` | boolean | Default privacy for groups created by the bot. | Always emitted. | Same API note. |
| `show_private_info` | boolean | Whether the bot shows the owner's private info without a flag. | Always emitted. | Import observation: `SystemConfigPatch.FromJson` does not read this key. |
| `member_limit` | number | `MemberLimitOverride`, or `Limits.MaxMemberCount` (`1000`) when the override is null. | Always a number. The unset override is not exported as null. | Import observation: `FromJson` does not read `member_limit`. |
| `group_limit` | number | `GroupLimitOverride`, or `Limits.MaxGroupCount` (`250`). | Always a number. | Import observation: `FromJson` does not read `group_limit`. |
| `case_sensitive_proxy_tags` | boolean | Case-sensitive proxy matching. | Always emitted. | |
| `proxy_error_message_enabled` | boolean | Whether proxy failures are shown. | Always emitted. | |
| `hid_display_split` | boolean | Whether the bot displays a 6-character id with a dash. | Always emitted. | Display only. Exported `id` strings are not split. |
| `hid_display_caps` | boolean | Whether the bot displays ids in uppercase. | Always emitted. | Display only. Exported ids are not rewritten by this flag. |
| `hid_list_padding` | string | List padding for 5-character ids. | Always emitted. | Source rule: `off`, `left`, or `right`. The sample uses `off`. The other two cannot be stored at the same time. Import observation: `FromJson` does not read this key. |
| `card_show_color_hex` | boolean | Whether profile cards show the hex color. | Always emitted. | Absent from the API system-settings table in `models.md`. |
| `proxy_switch` | string | What proxying does to the current switch. | Always emitted. | Source rule: `off`, `new`, or `add`. The sample uses `new`. |
| `name_format` | string or null | Webhook display-name format. | Always emitted. Null when unset. | API docs: default `{name} {tag}`. |
| `description_templates` | array of strings | Description templates. | Always emitted. | Import validation rejects more than 3 templates, and a template longer than `Limits.MaxDescriptionLength` (1000). Absent from the API system-settings table. |

`proxy_switch` meanings from `models.md`: `off` does nothing; `new` logs a new switch when the proxied member is absent; `add` starts a switch when the current one is empty, otherwise adds the member.

## Linked accounts

| Item | Value |
| --- | --- |
| Purpose | Discord accounts linked to the system. |
| JSON path | `$.accounts` |
| Source | `ModelRepository.GetSystemAccounts`, then `new JArray(list)` in `ExportSystem` |

```json
"accounts": [111111111111111111, 222222222222222222]
```

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `accounts[]` | number | Discord user id (`ulong`). | The array is always emitted. Elements are numbers, not strings. | Query: `select uid from accounts where system = ?`. No `ORDER BY`. |

The sample ids are fictional. They are larger than `2^53-1` (`9007199254740991`). A JSON parser that only has IEEE-754 numbers cannot keep them exact. The message model in `models.md` encodes Discord snowflakes as strings. This export path does not.

`ImportPluralKit` does not read `accounts`. Do not treat the array as an import contract.

## Member

| Item | Value |
| --- | --- |
| Purpose | One member in the owner export. |
| JSON path | `$.members[]` |
| Serializer | [`PKMemberExt.ToJson`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Models/PKMember.cs) |

Popeye (`aaaab`) carries several proxy tags, a birthday, aliases, and a last-message time. Penny (`aaaac`) carries null display name, birthday, pronouns, webhook avatar, banner, and description, plus an empty alias array. Gilligan (`aaaad`) carries color null and birthday `0004-07-04`.

`ToJson` has a `systemStr` parameter. `ExportSystem` does not pass it, so member objects in this file have no `system` key. `GET /members/:id` can include `system`. Those shapes are not the same.

`needsLegacyProxyTags` is a parameter on this commit and is unused in the method body. The export does not add top-level `prefix` or `suffix` fields.

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `id` | string | Member short id. | Always emitted. | 5 or 6 letters. See Identifiers. |
| `uuid` | string | Member UUID from `Guid.ToString()`. | Always emitted. | |
| `name` | string | Stored name for an owner export. | Always emitted. | For a non-owner, private name privacy substitutes `display_name`, or `name` when display name is null. API docs: 100-character limit. |
| `display_name` | string or null | Stored display name. | Always emitted for an owner. Null when unset. Penny is null. | A non-owner with private name privacy gets JSON `null` here even if a display name is stored. |
| `color` | string or null | Stored color. `ColorPrivacy` is commented out, so color is not passed through a privacy check. | Always emitted. Gilligan is null. | See Colors. |
| `birthday` | string or null | `LocalDate` export, or null. | Always emitted. Penny is null. | Format `yyyy-MM-dd`. See Timestamps. |
| `pronouns` | string or null | Pronouns. | Always emitted. | API docs: 100-character limit. |
| `avatar_url` | string or null | Avatar after CDN cleanup. | Always emitted. | See Images. |
| `webhook_avatar_url` | string or null | Separate webhook avatar after CDN cleanup. | Always emitted. Null when unset. | Import comment in `MemberPatch`: a webhook avatar equal to `avatar_url` is ignored on import. |
| `banner` | string or null | Banner after CDN cleanup. | Always emitted. | See Images. |
| `description` | string or null | Description. | Always emitted. | API docs: 1000-character limit. |
| `created` | string or null | Creation time. | Always emitted for an owner. | A non-owner with private metadata privacy gets null. |
| `keep_proxy` | boolean | Whether proxy tags stay in the sent message. | Always emitted. | |
| `tts` | boolean | Text-to-speech flag. | Always emitted. | |
| `autoproxy_enabled` | boolean or null | `AllowAutoproxy` for an owner. | Always emitted. Boolean in this owner export. | A non-owner export sets this key to JSON `null`, not an omission. |
| `message_count` | number or null | Message count. | Always a number for an owner, including `0`. | A non-owner with private metadata privacy gets null. |
| `last_message_timestamp` | string or null | Last proxied message time. | Always emitted. Null when there is no timestamp. | See Timestamps. |
| `proxy_tags` | array of objects | Proxy tags. | Always an array for an owner, including `[]`. | A non-owner with private proxy privacy gets `[]`, not null. See Proxy tag. |
| `aliases` | array of strings or null | Aliases. | An owner gets an array, including `[]`. | A non-owner with private alias privacy gets JSON `null`, not `[]`. |
| `privacy` | object | Member privacy. | Always an object for an owner. | A non-owner call sets `privacy` to JSON `null`. |

There is no archived flag, custom-front flag, or note id on this object.

## Member privacy

| Item | Value |
| --- | --- |
| JSON path | `$.members[].privacy` |
| Serializer | `PKMemberExt.ToJson` |

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `visibility` | string | Whether the member is visible as a member. | Always emitted. | `public` or `private`. |
| `name_privacy` | string | Name and display-name visibility. | Always emitted. | Same enum. |
| `description_privacy` | string | Description visibility. | Always emitted. | Same enum. |
| `banner_privacy` | string | Banner visibility. | Always emitted. | Same enum. |
| `birthday_privacy` | string | Birthday visibility. | Always emitted. | Same enum. |
| `pronoun_privacy` | string | Pronoun visibility. | Always emitted. | Same enum. |
| `avatar_privacy` | string | Avatar and webhook-avatar visibility. | Always emitted. | Same enum. |
| `metadata_privacy` | string | Created time, message count, and last message time. | Always emitted. | Same enum. |
| `proxy_privacy` | string | Proxy-tag visibility. | Always emitted. | Same enum. |
| `alias_privacy` | string | Alias visibility. | Always emitted. | Same enum. |

## Proxy tag

| Item | Value |
| --- | --- |
| Purpose | One prefix/suffix pair. |
| JSON path | `$.members[].proxy_tags[]` |
| Serializer | `PKMemberExt.ToJson`, using [`ProxyTag`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Models/ProxyTag.cs) |

Popeye has three tags: both sides, prefix only, and suffix only. Those are three objects. One object cannot be both prefix-only and suffix-only.

```json
{ "prefix": "P:", "suffix": ":P" }
```

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `prefix` | string or null | Text before the message. | Always emitted. Null when that side is unused. | The constructor stores an empty string as null. |
| `suffix` | string or null | Text after the message. | Always emitted. Null when that side is unused. | Same empty-string rule. |

`ProxyTag.Valid` requires a non-null prefix or suffix, and `prefix + "text" + suffix` no longer than `Limits.MaxProxyTagLength` (100). The serializer does not check `Valid`. It writes the stored prefix and suffix. The sample tags are non-empty.

## Group

| Item | Value |
| --- | --- |
| Purpose | One group and its member short ids. |
| JSON path | `$.groups[]` |
| Serializer | [`PKGroupExt.ToJson`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Models/PKGroup.cs) with `needsMembersArray: true` |

Theatre contains `aaaab` and `aaaad`. Backstage contains `aaaac` and `aaaab`. Popeye is in both groups. Wings has `"members": []`. Groups are not nested: there is no parent id.

`ExportSystem` does not pass `systemStr`, so these objects omit `system`. A single-group API response can include it.

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `id` | string | Group short id. | Always emitted. | |
| `uuid` | string | Group UUID. | Always emitted. | |
| `name` | string or null | Group name for an owner export. | Always emitted. | API docs: 100-character limit. |
| `display_name` | string or null | Display name. | Always emitted for an owner. | Same non-owner null rule as members. |
| `description` | string or null | Description. | Always emitted. | API docs: 1000-character limit. |
| `icon` | string or null | Icon after CDN cleanup. | Always emitted. | See Images. |
| `banner` | string or null | Banner string as stored. | Always emitted. | This call does not run `TryGetCleanCdnUrl` on the group banner. Icon, system banner, and member banner do. |
| `color` | string or null | Stored color. | Always emitted. Backstage and Wings are null. | See Colors. |
| `created` | string or null | Creation time. | Always emitted for an owner. | Private metadata privacy hides it from a non-owner. |
| `members` | array of strings | Member short ids. | Always emitted on this export path, including `[]`. | Each string is `members.hid` from `GetGroupMemberInfo`, not the member UUID. `MemberUuid` is selected and not written. |
| `privacy` | object | Group privacy. | Always an object for an owner. | Non-owner: JSON `null`. |

`GetGroupMemberInfo` has no `ORDER BY`. The sample order is a fictional result, not a required order.

## Group privacy

| Item | Value |
| --- | --- |
| JSON path | `$.groups[].privacy` |
| Serializer | `PKGroupExt.ToJson` |

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `name_privacy` | string | Name visibility. | Always emitted. | `public` or `private`. |
| `description_privacy` | string | Description visibility. | Always emitted. | Same enum. |
| `banner_privacy` | string | Banner visibility. | Always emitted. | Same enum. |
| `icon_privacy` | string | Icon visibility. | Always emitted. | Same enum. |
| `list_privacy` | string | List visibility. | Always emitted. | Same enum. |
| `metadata_privacy` | string | Creation-time visibility. | Always emitted. | Same enum. |
| `visibility` | string | Whether the group itself is visible. | Always emitted. | Same enum. The key is `visibility`, not `group_privacy`. |

## Switch records

| Item | Value |
| --- | --- |
| Purpose | One recorded front, reduced to a time and member short ids. |
| JSON path | `$.switches[]` |
| Serializer | `DataFileService.ExportSystem`, using `GetPeriodFronters` |

```json
{ "timestamp": "2026-01-03T12:00:00Z", "members": ["aaaab", "aaaac"] }
```

The sample has three switches, newest first: Popeye with Penny, an empty member list, and Gilligan alone.

| Field | JSON type | Meaning | Null/omission behavior | References/constraints |
| --- | --- | --- | --- | --- |
| `timestamp` | string | `SwitchListEntry.TimespanStart` formatted for export. | Always emitted. | Not the switch UUID. See Timestamps. |
| `members` | array of strings | Member short ids in that switch. | Always emitted. `[]` is a switch with no members. | Values are `PKMember.Hid`. They are not UUIDs and not member objects. `Limits.MaxSwitchMemberCount` is 150. |

`GetSwitchMembersList` orders by `switches.timestamp DESC`. `GetPeriodFronters` keeps that newest-first order. The export uses the full range from `DateTime.MinValue` through the clock, so this is a history dump rather than the 100-row API page.

A switch with no `switch_members` rows survives as an empty `members` array because the query is a left join and `Member != default` drops the empty side.

This object has no `id`. The API switch model has a UUID `id`. `GET /systems/:id/switches` returns member short ids. `GET /systems/:id/fronters` returns full member objects. The export matches neither extra field.

## Identifiers

Every system, member, and group has a short id and a UUID. Switches in this export have neither.

[`HidUtils.ParseHid`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Database/Utils/HidUtils.cs) lowercases, removes `-`, and accepts `^[a-zA-Z]{5,6}$`. The sample uses five lowercase letters: `aaaaa` through `aaaag`. A 6-character id, a dashed display form, and uppercase display are bot or API input forms. This export writes the stored trimmed hid, not `HidTransform` output.

`models.md` says a short id is unique per resource, so a member and a system may share one. UUIDs are the long ids. `Guid.ToString()` with no format is the 8-4-4-4-12 lowercase form. The sample UUIDs are version 4: the version nibble is `4` and the variant nibble is `8`, `9`, `a`, or `b`.

Which reference uses which id:

| Use | Id type |
| --- | --- |
| `$.id`, `$.members[].id`, `$.groups[].id` | short id |
| `uuid` on system, member, and group | UUID string |
| `$.groups[].members[]` | member short id |
| `$.switches[].members[]` | member short id |
| `$.accounts[]` | Discord snowflake as a JSON number |

## Colors

`models.md` describes color as a 6-character hex code with no leading `#`. Member import lowercases the string and checks `^[0-9a-fA-F]{6}$`. System import checks the same pattern and does not lowercase in `SystemPatch.FromJSON`. The export writes the stored string unchanged.

The sample uses lowercase `aabbcc`, `4a90e2`, `ff8800`, and `336699`, and JSON `null` where no color is stored. `#4a90e2` is not this format. Uppercase hex and lowercase hex cannot both be the stored value.

## Timestamps and birthdays

[`DateTimeFormats.FormatExport`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Utils/DateTimeFormats.cs):

| Value | Pattern |
| --- | --- |
| `Instant` | NodaTime `InstantPattern.ExtendedIso` |
| `LocalDate` | `yyyy-MM-dd` |

`ExtendedIso` is an ISO-8601 instant ending in `Z`. Fractional seconds are included only when the instant is not a whole second, and trailing zeros in the fraction are omitted. Every instant in the sample is a whole second, so the text has no decimal.

Birthday export uses `FormatExport` on the `LocalDate`, not `BirthdayString`. `BirthdayString` hides a year of `0001` or `0004` in bot display. The export still writes the full date. Gilligan's `0004-07-04` is that sentinel, not a display abbreviation. A known year and `0004` cannot both be stored on one member. Penny's birthday is JSON `null`.

## Images

`TryGetCleanCdnUrl` rewrites a Discord media-proxy attachment URL to `https://cdn.discordapp.com/attachments/...`. Other strings, including `https://example.com/...`, pass through. The sample uses `example.com` URLs. Those hosts are reserved examples, not live webhook endpoints.

Cleanup is applied to the system avatar, system banner, member avatar, member webhook avatar, member banner, and group icon. The group banner is written from `BannerImage` with no cleanup call.

`Limits.MaxUriLength` is 256. Import checks absolute `https` URLs for member avatars. The sample URLs are `https`.

## API records that this export does not contain

These appear in `models.md` or the v2 controllers and are not objects in `ExportSystem`:

- Message model.
- System guild settings.
- Autoproxy settings.
- Member guild settings.
- A switch UUID, and a fronter payload of full member objects.
- `system` on member and group objects.

`models.md` also omits `description_templates` and `card_show_color_hex`, which this export config does emit. `webhook_url` is in the owner export and is not in the published system model table.

## Shared-feed data with no field in this export

The common model feed can carry records this serializer does not write. This sample does not invent keys for them.

| Feed data | What this export can hold |
| --- | --- |
| Place, nested system, or parent group | Not present. Groups are a flat array. |
| Anchor or member relationship | Not present. |
| Custom field definition or value | Not present. |
| Note body | Not present. A member `description` is a different string. |
| Friend, privacy bucket, or audience other than public/private | Not present. Privacy is only `public` and `private`. |
| Custom front that is not a member | Not present. Switches point at member short ids. |
| Archive flag or archive reason | Not present. |
| Account email, account permission, or operation role | Not present. `accounts` is only Discord user ids. |
| Embedded avatar bytes | Not present. Avatars are URL strings or null. |
| Open front period with an end time and a role | A switch has a timestamp and member ids. It has no `ended_at` and no role. |

## Import

`ExportSystem` is the authority for the file this note describes. [`BulkImporter.ImportPluralKit`](https://github.com/PluralKit/PluralKit/blob/22fa0682e4fef3b8fb97b09ea3320b4d2cd738dc/PluralKit.Core/Utils/BulkImporter/PluralKitImport.cs) reads system fields, optional `config`, `members`, optional `groups`, and `switches`. On this commit it does not read `version` or `accounts`. `SystemPatch.FromJSON` does not read `webhook_url`, `id`, `uuid`, or `created`. `SystemConfigPatch.FromJson` does not read `show_private_info`, `member_limit`, `group_limit`, or `hid_list_padding`. An unknown `proxy_switch` string is stored as `off`.

Those are observations about this commit. They are not a statement that import will accept every key this sample contains.
