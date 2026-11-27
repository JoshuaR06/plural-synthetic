# Simply Plural source inventory and synthetic-output reference

Analysis date: 26 November 2026. Evidence: the four files supplied with this request. This is a specimen-based reference, not a claim that every historical SP feature or field is known.

## 1. Source identity and provenance

| Source | Observed contents | Role in this analysis |
| --- | --- | --- |
| `export_bVP6Jt40jqYWC2tfp54TZlg0sqq2.json` | One JSON object with 43 collection arrays; 23 non-empty collections. | Broadest direct-export specimen; user identifies it as a file in Joshua’s repository. Its contents include personal records and operational/authentication data. Repository location does not make it synthetic. |
| `simplyplural-official.json` | One JSON object with 8 collection arrays; 5 fictional members and 6 groups. | Existing synthetic subset. Its filename alone does not establish complete SP coverage. |
| `sp_export.zip` | 117 ZIP entries: 66 JSON files, 47 PNGs, one Thumbs.db, and directory entries. Includes API wrappers, per-member notes, and a capture manifest. | API-capture/breakout evidence; retains shapes absent from the smaller synthetic subset. Thumbs.db is a Windows image cache, not an SP account database. |
| `sp.zip` | 14 root JSON files including a conversion manifest and duplicated user/me profiles. | User identifies this as the original unmodified export archive. Its packaged contents are a breakout representation: manifest source_format is official_simply_plural_export_probe, and input_file_name names another source JSON. Preserve the user-provided provenance while recording this observable distinction. |

The files are not interchangeable snapshots. The broad export has 51 members, 2 groups, 3 buckets, and 4 notes. Both breakout archives have 49 members, no groups, and 2 buckets. These differences must not be silently reconciled or described as conversion loss without the upstream conversion history.

`sp.zip` manifest lists `notes/` with count 2, but no notes folder or note files are packaged. `sp_export.zip` actually contains four note records spread over 49 numbered note files; the other files are empty arrays. The capture includes 892 front-history rows plus a separate 889-row start/end query result; the latter is not a second set to concatenate.

## 2. Collection coverage

A dash means the collection/file is not present. Zero means an observed empty array. Non-empty specimens establish fields; empty arrays do not establish record schemas.

| Collection | Broad export | Existing synthetic | sp.zip | API capture |
| --- | ---: | ---: | ---: | ---: |
| `securityLogs` | 38 | — | — | — |
| `events` | 0 | — | — | — |
| `private` | 1 | — | — | — |
| `sharedFront` | 1 | — | — | — |
| `channelCategories` | 1 | — | 1 | 1 |
| `automatedReminders` | 0 | — | 0 | 0 |
| `repeatedRemidners` | 0 | — | — | — |
| `avatarExports` | 6 | — | — | — |
| `boardMessages` | 3 | — | — | — |
| `customFields` | 7 | 2 | 7 | 7 |
| `repeatedReminders` | 0 | — | 0 | 0 |
| `undeliveredMessages` | 0 | — | — | — |
| `serverData` | 2 | — | — | — |
| `cancelFeedback` | 0 | — | — | — |
| `pendingFriendRequests` | 0 | — | — | — |
| `polls` | 0 | — | 0 | 0 |
| `fronters` | 0 | — | — | — |
| `subscribers` | 0 | — | — | — |
| `dataExports` | 5 | — | — | — |
| `users` | 1 | 1 | 1 | 1 |
| `tokens` | 1 | — | — | — |
| `channels` | 6 | — | 6 | 6 |
| `queuedEvents` | 0 | — | — | — |
| `test` | 0 | — | — | — |
| `reports` | 7 | — | — | — |
| `notes` | 4 | 2 | — (manifest: 2) | 4 |
| `members` | 51 | 5 | 49 | 49 |
| `messages` | 0 | — | — | — |
| `privateFront` | 1 | — | — | — |
| `comments` | 0 | — | — | — |
| `notifications` | 0 | — | — | — |
| `chatMessages` | 7 | — | — | — |
| `groups` | 2 | 6 | 0 | 0 |
| `privacyBuckets` | 3 | 2 | 2 | 2 |
| `potato` | 0 | — | — | — |
| `views` | 0 | — | — | — |
| `friends` | 2 | — | 2 | 2 |
| `verifiedKeys` | 0 | — | — | — |
| `frontHistory` | 892 | 6 | 892 | 892 |
| `invalidJwtTokens` | 0 | — | — | — |
| `usage` | 17 | — | — | — |
| `frontStatuses` | 1 | 1 | — | 0 |
| `socketNotifications` | 0 | — | — | — |

The broad specimen contains both `repeatedRemidners` and `repeatedReminders`. Preserve their distinct observed spellings in the inventory; neither has a non-empty record from which to infer a schema.

## 3. Serialization shapes

### Direct export

One root object contains collection arrays. Records have `_id` directly:

```json
{"members":[{"_id":"synthetic-member-0001","uid":"synthetic-system-0001","name":"Nova"}]}
```

No PB `account` envelope or `pluralBridgeExport` header belongs inside this target format.

### API capture

Most collection responses use `{exists,id,content}` records. `me` and `user` are single wrapped objects. Some numbered note files instead contain a direct note object or an array. Inspect each response shape; do not apply one wrapper rule blindly.

```json
{"exists":true,"id":"synthetic-member-0001","content":{"name":"Nova","uid":"synthetic-system-0001"}}
```

To normalize a successful wrapped record, use `id` as `_id` and keep `content`. A false `exists` flag is not a member payload.

### Breakout archive

Collection files hold direct arrays. `me.json` and `user.json` hold a direct profile object and are equivalent views of one profile, not two accounts. `manifest.json` records conversion provenance; it is not an SP data collection.


## 4. Observed non-empty record types

These tables cover top-level record fields across all four specimens. Presence counts are for the broad export where a collection is non-empty; additional fields from other specimens are listed with their own evidence. A field name suggests intent in some operational collections; those descriptions are provisional unless a reference rule below confirms the association.

### `securityLogs[]`

Authentication/security history. Broad-export records: 38.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 38/38 | Record identifier within its collection. |
| `action` | string | 38/38 | Security-log operation description/code. |
| `at` | integer | 38/38 | Security-log integer timestamp. |
| `ip` | string | 38/38 | Security-log IP address; personal operational data. |
| `uid` | string | 38/38 | Owning user/system identifier where used as ownership; compare the collection context. |

### `private[]`

Private account settings and operational state. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `auditContentChanges` | boolean | 1/1 | Audit-content preference. |
| `auditRetention` | integer | 1/1 | Audit-retention value; units unresolved. |
| `categories` | array | 1/1 | Category reference array in private settings. |
| `defaultPrivacySettings` | object | 1/1 | Per-resource default bucket/audience arrays on the private settings record. |
| `generationsLeft` | integer | 1/1 | Stored remaining-generation count. |
| `hideAudits` | boolean | 1/1 | Audit-display preference. |
| `lastExport` | integer | 1/1 | Export timestamp value. |
| `lastExportAttempt` | integer | 1/1 | Export-attempt timestamp value. |
| `lastGenerationReset` | integer | 1/1 | Generation-counter reset timestamp. |
| `lastOperationTime` | integer | 1/1 | Last-operation integer timestamp. |
| `lastRefresh` | integer | 1/1 | Refresh timestamp value. |
| `latestVersion` | integer | 1/1 | Stored client/version marker. |
| `location` | string | 1/1 | Stored location value; personal operational data. |
| `notificationHistory` | array | 1/1 | Nested notification-history records. |
| `notificationToken` | array | 1/1 | Push-notification token collection; never copied into synthetic output. |
| `termsOfServiceAccepted` | boolean | 1/1 | Observed acceptance flag; both spellings coexist. |
| `termsOfServicesAccepted` | boolean | 1/1 | Observed acceptance flag; distinct spelling retained in the source. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |

### `sharedFront[]`

Shared front-summary cache. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `beforeCustomFrontString` | string | 1/1 | Prior cached custom-front text. |
| `beforeFrontNotificationString` | string | 1/1 | Prior cached front-notification text. |
| `customFrontString` | string | 1/1 | Cached/rendered custom-front text. |
| `customFronters` | array | 1/1 | Current custom-front identifier array on a front summary. |
| `frontNotificationString` | string | 1/1 | Cached front-notification text. |
| `frontString` | string | 1/1 | Cached/rendered front text. |
| `fronters` | array | 1/1 | Current member identifier array on a front summary. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |

### `channelCategories[]`

Chat channel categories. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `channels` | array | 1/1 | Channel identifier array on a category. |
| `desc` | string | 1/1 | Description text. |
| `lastOperationTime` | integer | 1/1 | Last-operation integer timestamp. |
| `name` | string | 1/1 | Display label. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |

### `avatarExports[]`

Avatar-export access/download records. Broad-export records: 6.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 6/6 | Record identifier within its collection. |
| `downloads` | integer | 5/6 | Download counter. |
| `exp` | integer | 6/6 | Expiry value on an export-access record; units require verification. |
| `key` | string | 6/6 | Export/download access key; never copied into synthetic output. |
| `lastDownload` | integer | 5/6 | Last-download timestamp value. |
| `uid` | string | 6/6 | Owning user/system identifier where used as ownership; compare the collection context. |

### `boardMessages[]`

Member board messages. Broad-export records: 3.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 3/3 | Record identifier within its collection. |
| `lastOperationTime` | integer | 3/3 | Last-operation integer timestamp. |
| `message` | string | 3/3 | Message content; some chat rows also carry an iv and may be encrypted. |
| `read` | boolean | 3/3 | Read state. |
| `supportMarkdown` | boolean | 3/3 | Markdown flag with singular support spelling; null also occurs on migrated field definitions. |
| `title` | string | 3/3 | Title text. |
| `uid` | string | 3/3 | Owning user/system identifier where used as ownership; compare the collection context. |
| `writtenAt` | integer | 3/3 | Message integer timestamp. |
| `writtenBy` | string | 3/3 | Message author identifier. |
| `writtenFor` | string | 3/3 | Message recipient identifier. |

### `customFields[]`

Custom-field definitions. Broad-export records: 7.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 7/7 | Record identifier within its collection. |
| `buckets` | array | 7/7 | References to privacy-bucket records. Visibility/audience association, not an edit-permission list. |
| `name` | string | 7/7 | Display label. |
| `oid` | string | 7/7 | Legacy identifier on a migrated custom field; matches a users.fields key in the broad export. |
| `order` | string | 7/7 | Field ordering token; integers and rank strings are both observed. |
| `supportMarkdown` | null | 7/7 | Markdown flag with singular support spelling; null also occurs on migrated field definitions. |
| `type` | integer | 7/7 | Numeric custom-field type code. Complete code meanings are not established by these specimens. |
| `uid` | string | 7/7 | Owning user/system identifier where used as ownership; compare the collection context. |

Additional fields seen only in another supplied specimen:
- `preventTrusted` (boolean): Legacy trusted-audience privacy flag; exact interaction requires the SP behavior contract.
- `private` (boolean): Legacy privacy flag; exact interaction with buckets requires the SP behavior contract.

### `serverData[]`

Server-side per-user state. Broad-export records: 2.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 2/2 | Record identifier within its collection. |
| `lastReadMessage` | integer | 1/2 | Server message-read position value. |
| `migrated` | boolean | 1/2 | Migration-state flag on server data. |
| `uid` | string | 2/2 | Owning user/system identifier where used as ownership; compare the collection context. |

### `dataExports[]`

Export access/download records. Broad-export records: 5.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 5/5 | Record identifier within its collection. |
| `downloads` | integer | 5/5 | Download counter. |
| `exp` | integer | 5/5 | Expiry value on an export-access record; units require verification. |
| `key` | string | 5/5 | Export/download access key; never copied into synthetic output. |
| `lastDownload` | integer | 5/5 | Last-download timestamp value. |
| `uid` | string | 5/5 | Owning user/system identifier where used as ownership; compare the collection context. |

### `users[]`

User/system profile. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `avatarUrl` | string | 1/1 | Avatar URL reference. |
| `color` | string | 1/1 | Display color string; preserve its observed representation. |
| `desc` | string | 1/1 | Description text. |
| `fields` | object | 1/1 | Embedded legacy field-definition map on a user. Keys differ from migrated customFields IDs in the broad export. |
| `frame` | object | 1/1 | Avatar decoration/frame object; often empty. |
| `isAsystem` | boolean | 1/1 | User/system classification flag; preserve this exact spelling. |
| `lastOperationTime` | integer | 1/1 | Last-operation integer timestamp. |
| `supportDescMarkdown` | boolean | 1/1 | Markdown flag for a description. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |
| `username` | string | 1/1 | User/system display or account name. |

### `tokens[]`

Authentication token records. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `permission` | integer | 1/1 | Token permission code; distinct from PB permissions. Its vocabulary is not established here. |
| `token` | string | 1/1 | Authentication token; never copied into synthetic output. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |

### `channels[]`

Chat channels. Broad-export records: 6.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 6/6 | Record identifier within its collection. |
| `desc` | string | 6/6 | Description text. |
| `lastOperationTime` | integer | 6/6 | Last-operation integer timestamp. |
| `name` | string | 6/6 | Display label. |
| `uid` | string | 6/6 | Owning user/system identifier where used as ownership; compare the collection context. |

### `reports[]`

Generated report records. Broad-export records: 7.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 7/7 | Record identifier within its collection. |
| `createdAt` | integer | 7/7 | Report creation timestamp. |
| `uid` | string | 7/7 | Owning user/system identifier where used as ownership; compare the collection context. |
| `url` | string | 7/7 | Report URL; may contain access information. |
| `usedSettings` | object | 7/7 | Nested report-generation settings. |

### `notes[]`

Member-associated notes. Broad-export records: 4.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 4/4 | Record identifier within its collection. |
| `color` | string | 4/4 | Display color string; preserve its observed representation. |
| `date` | integer | 4/4 | Note date represented as an integer timestamp. |
| `lastOperationTime` | integer | 4/4 | Last-operation integer timestamp. |
| `member` | string | 4/4 | Note owner/member reference, or front-history participant; custom fronts refer to frontStatuses. |
| `note` | string | 4/4 | Note body. |
| `supportMarkdown` | boolean | 4/4 | Markdown flag with singular support spelling; null also occurs on migrated field definitions. |
| `title` | string | 4/4 | Title text. |
| `uid` | string | 4/4 | Owning user/system identifier where used as ownership; compare the collection context. |

### `members[]`

Member profiles and their field values. Broad-export records: 51.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 51/51 | Record identifier within its collection. |
| `archived` | boolean | 31/51 | Member archive flag; spelling differs from PB isArchived. |
| `archivedReason` | string | 31/51 | Archive explanation text. |
| `avatarUrl` | string | 51/51 | Avatar URL reference. |
| `avatarUuid` | string | 49/51 | Avatar identifier/reference, not embedded image bytes. |
| `buckets` | array | 51/51 | References to privacy-bucket records. Visibility/audience association, not an edit-permission list. |
| `color` | string | 51/51 | Display color string; preserve its observed representation. |
| `desc` | string | 51/51 | Description text. |
| `frame` | object | 49/51 | Avatar decoration/frame object; often empty. |
| `info` | object | 38/51 | Member custom-field values keyed by customFields._id in these supplied files. |
| `lastOperationTime` | integer | 51/51 | Last-operation integer timestamp. |
| `name` | string | 51/51 | Display label. |
| `pkId` | string | 49/51 | External/member-link identifier; exact contract not established here. |
| `preventTrusted` | boolean | 44/51 | Legacy trusted-audience privacy flag; exact interaction requires the SP behavior contract. |
| `preventsFrontNotifs` | boolean | 49/51 | Front-notification suppression flag. |
| `private` | boolean | 44/51 | Legacy privacy flag; exact interaction with buckets requires the SP behavior contract. |
| `pronouns` | string | 51/51 | Pronoun text. |
| `receiveMessageBoardNotifs` | boolean | 31/51 | Member message-board notification flag. |
| `supportDescMarkdown` | boolean | 51/51 | Markdown flag for a description. |
| `uid` | string | 51/51 | Owning user/system identifier where used as ownership; compare the collection context. |

### `privateFront[]`

Private front-summary cache. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `beforeCustomFrontString` | string | 1/1 | Prior cached custom-front text. |
| `beforeFrontNotificationString` | string | 1/1 | Prior cached front-notification text. |
| `customFrontString` | string | 1/1 | Cached/rendered custom-front text. |
| `customFronters` | array | 1/1 | Current custom-front identifier array on a front summary. |
| `frontNotificationString` | string | 1/1 | Cached front-notification text. |
| `frontString` | string | 1/1 | Cached/rendered front text. |
| `fronters` | array | 1/1 | Current member identifier array on a front summary. |
| `private` | boolean | 1/1 | Legacy privacy flag; exact interaction with buckets requires the SP behavior contract. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |

### `chatMessages[]`

Chat-message records. Broad-export records: 7.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 7/7 | Record identifier within its collection. |
| `channel` | string | 7/7 | Chat channel reference. |
| `iv` | string | 7/7 | Cryptographic initialization-vector field; algorithm cannot be inferred from this alone. |
| `lastOperationTime` | integer | 7/7 | Last-operation integer timestamp. |
| `message` | string | 7/7 | Message content; some chat rows also carry an iv and may be encrypted. |
| `uid` | string | 7/7 | Owning user/system identifier where used as ownership; compare the collection context. |
| `writer` | string | 7/7 | Writer identifier. |
| `writtenAt` | integer | 7/7 | Message integer timestamp. |

### `groups[]`

Groups, parent links, and member associations. Broad-export records: 2.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 2/2 | Record identifier within its collection. |
| `buckets` | array | 2/2 | References to privacy-bucket records. Visibility/audience association, not an edit-permission list. |
| `color` | string | 2/2 | Display color string; preserve its observed representation. |
| `desc` | string | 2/2 | Description text. |
| `emoji` | string | 2/2 | Emoji/icon text. |
| `lastOperationTime` | integer | 2/2 | Last-operation integer timestamp. |
| `members` | array | 2/2 | Member identifier array on a group. |
| `name` | string | 2/2 | Display label. |
| `parent` | string | 2/2 | Parent group identifier; the supplied synthetic sample uses the literal root for top-level groups. |
| `supportDescMarkdown` | boolean | 2/2 | Markdown flag for a description. |
| `uid` | string | 2/2 | Owning user/system identifier where used as ownership; compare the collection context. |

### `privacyBuckets[]`

Named privacy/audience buckets. Broad-export records: 3.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 3/3 | Record identifier within its collection. |
| `color` | string | 3/3 | Display color string; preserve its observed representation. |
| `desc` | string | 3/3 | Description text. |
| `icon` | string | 3/3 | Privacy-bucket icon text. |
| `lastOperationTime` | integer | 1/3 | Last-operation integer timestamp. |
| `name` | string | 3/3 | Display label. |
| `rank` | string | 3/3 | Ordering token on a privacy bucket. |
| `uid` | string | 3/3 | Owning user/system identifier where used as ownership; compare the collection context. |

### `friends[]`

Friend relationships and sharing preferences. Broad-export records: 2.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 2/2 | Record identifier within its collection. |
| `buckets` | array | 2/2 | References to privacy-bucket records. Visibility/audience association, not an edit-permission list. |
| `customFrontString` | string | 2/2 | Cached/rendered custom-front text. |
| `frienduid` | string | 2/2 | Identifier of the other user in a friendship. |
| `frontNotificationString` | string | 2/2 | Cached front-notification text. |
| `frontString` | string | 2/2 | Cached/rendered front text. |
| `getFrontNotif` | boolean | 2/2 | Friendship notification preference. |
| `getTheirFrontNotif` | boolean | 1/2 | Other-direction front-notification preference. |
| `lastOperationTime` | integer | 1/2 | Last-operation integer timestamp. |
| `seeFront` | boolean | 2/2 | Friendship setting for front visibility. |
| `seeMembers` | boolean | 2/2 | Friendship setting for member visibility. |
| `trusted` | boolean | 2/2 | Friend trust flag. |
| `uid` | string | 2/2 | Owning user/system identifier where used as ownership; compare the collection context. |

Additional fields seen only in another supplied specimen:
- `avatarUrl` (string): Avatar URL reference.
- `color` (string): Display color string; preserve its observed representation.
- `desc` (string): Description text.
- `fields` (object): Embedded legacy field-definition map on a user. Keys differ from migrated customFields IDs in the broad export.
- `frame` (object): Avatar decoration/frame object; often empty.
- `isAsystem` (boolean): User/system classification flag; preserve this exact spelling.
- `supportDescMarkdown` (boolean): Markdown flag for a description.
- `username` (string): User/system display or account name.

### `frontHistory[]`

Per-member/custom-front history rows. Broad-export records: 892.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 892/892 | Record identifier within its collection. |
| `custom` | boolean | 892/892 | Selects ordinary-member versus custom-front participation. |
| `customStatus` | string | 29/892 | Free-text status on a front event; it is not the custom-front identifier. |
| `endTime` | integer | 890/892 | Front-history end as an integer timestamp. Absent on the two live rows in the broad export. |
| `lastOperationTime` | integer | 892/892 | Last-operation integer timestamp. |
| `live` | boolean | 892/892 | Front-history live/open flag; validate alongside endTime. |
| `member` | string | 892/892 | Note owner/member reference, or front-history participant; custom fronts refer to frontStatuses. |
| `startTime` | integer | 892/892 | Front-history start as an integer timestamp; observed values are consistent with Unix milliseconds. |
| `uid` | string | 892/892 | Owning user/system identifier where used as ownership; compare the collection context. |

### `usage[]`

API usage counters and expiration. Broad-export records: 17.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `DELETE - /v1/member/:id` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/auth/logs` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/board/member/:id` | integer | 3/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/board/unread` | integer | 12/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/customFields/:system` | integer | 6/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/friends/` | integer | 13/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/friends/getFrontValues` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/friends/settings` | integer | 13/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/frontHistory/:system` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/frontHistory/member/:id` | integer | 3/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/groups/:system` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/me` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/notes/:system/:member` | integer | 3/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/privacyBuckets` | integer | 12/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/user/:id` | integer | 15/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/user/:id/reports` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `GET - /v1/user/analytics` | integer | 2/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/customField/order` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/customFront/:id` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/group/:id` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/group/members` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/member/:id` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/privacyBucket/assignfriends` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/privacyBucket/order` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/privacyBucket/setbuckets` | integer | 2/17 | Per-route usage counter; method and path form the key. |
| `PATCH - /v1/user/:id` | integer | 4/17 | Per-route usage counter; method and path form the key. |
| `POST - /v1/board/:id?` | integer | 2/17 | Per-route usage counter; method and path form the key. |
| `POST - /v1/customFront/:id?` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `POST - /v1/member/:id?` | integer | 2/17 | Per-route usage counter; method and path form the key. |
| `POST - /v1/note/:id?` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `POST - /v1/privacyBucket/:id?` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `POST - /v1/user/:id/export` | integer | 3/17 | Per-route usage counter; method and path form the key. |
| `POST - /v2/group/:id?` | integer | 1/17 | Per-route usage counter; method and path form the key. |
| `_id` | string | 17/17 | Record identifier within its collection. |
| `expireAt` | string | 17/17 | Usage-record expiration string. |
| `uid` | string | 17/17 | Owning user/system identifier where used as ownership; compare the collection context. |

### `frontStatuses[]`

Custom-front definitions. Broad-export records: 1.

| Field | Observed JSON types | Broad presence | Meaning / limit |
| --- | --- | ---: | --- |
| `_id` | string | 1/1 | Record identifier within its collection. |
| `avatarUrl` | string | 1/1 | Avatar URL reference. |
| `avatarUuid` | string | 1/1 | Avatar identifier/reference, not embedded image bytes. |
| `buckets` | array | 1/1 | References to privacy-bucket records. Visibility/audience association, not an edit-permission list. |
| `color` | string | 1/1 | Display color string; preserve its observed representation. |
| `desc` | string | 1/1 | Description text. |
| `frame` | object | 1/1 | Avatar decoration/frame object; often empty. |
| `lastOperationTime` | integer | 1/1 | Last-operation integer timestamp. |
| `name` | string | 1/1 | Display label. |
| `preventTrusted` | boolean | 1/1 | Legacy trusted-audience privacy flag; exact interaction requires the SP behavior contract. |
| `preventsFrontNotifs` | boolean | 1/1 | Front-notification suppression flag. |
| `private` | boolean | 1/1 | Legacy privacy flag; exact interaction with buckets requires the SP behavior contract. |
| `supportDescMarkdown` | boolean | 1/1 | Markdown flag for a description. |
| `uid` | string | 1/1 | Owning user/system identifier where used as ownership; compare the collection context. |

## 5. Nested records and key relationships

- `members[].info` is an object mapping a custom-field identifier to its value. All seven distinct value keys in the broad export resolve to `customFields[]._id`. Values in the supplied specimens are strings. Do not replace value keys with field names.
- `users[].fields` is a legacy object keyed by field identifiers. Its definition records contain `name`, `order`, `private`, `preventTrusted`, and `type`. In the broad export its keys correspond to `customFields[].oid`, while member values use the migrated `_id`. Retain this alias relationship when analyzing historical files; do not emit duplicate definitions as independent fields.
- `members[].frame` is often empty. Observed non-empty frame properties across members/custom fronts are `bgShape`, `bgClip`, `bgStartColor`, and `bgEndColor`; values are strings. This does not establish the complete frame schema.
- `private[].defaultPrivacySettings` has `members`, `groups`, `customFronts`, and `customFields` arrays. These are visibility settings, not edit-authority roles.
- `private[].notificationHistory[]` records have `timestamp` (integer), `title` (string), and `message` (string). `notificationToken` contains strings. Neither collection is copied into synthetic output.
- `reports[].usedSettings` has `sendTo`, `cc`, and resource settings for `customFronts`, `frontHistory`, and `members`. These are report options. Actual recipient details and report URLs are not copied into output.
- `groups[].parent` is `root` for top-level groups in the supplied synthetic sample; nested groups reference another group `_id`.
- `groups[].members[]` references member `_id`. A member may appear in several groups while retaining one member record.
- `notes[].member` references a member `_id`; title/body use `title` and `note`, not PB `body`.
- `frontHistory[].member` references a member `_id` when `custom` is false, or a `frontStatuses` record when `custom` is true. `customStatus` is separate text.
- `frontHistory[].startTime` and optional `endTime` are integer millisecond timestamps in the reference output. Both supplied direct-export specimens omit `endTime` on two current rows; they do not use JSON null there.
- One SP front-history row identifies one participant. Several concurrent rows represent co-fronting. A PB event with multiple `memberIds` requires several SP rows if that mapping is approved.
- `buckets[]` references privacy-bucket `_id` on members and, in the broad specimen, custom fields, groups, custom fronts, and friends. Bucket membership concerns sharing audiences. It does not establish read/create/update/delete permission mappings.

### Reference audit of the supplied data

The broad direct export resolves group member references, note owners, member bucket references, member custom-field value keys, and normal front-history participant references within the supplied collections.

The existing eight-collection synthetic file contains one front-history reference to `synthetic-member-deleted-0099`, which has no member record. Treat this as an explicit deleted-member test case rather than a clean-reference guarantee. It has a valid custom-front reference as well.

The breakout sources are not required to resolve all history references to their current 49 members. Deleted or absent historical members are a condition for an importer to report or handle, not permission to invent real people.

## 6. What the specimens establish, and what remains unknown

Established structural evidence includes members, groups and nested group parents, repeated group membership, field definitions and values, note ownership, buckets, archived members, custom fronts, current/open fronts, and millisecond timestamps.

The broad export also contains chat/channel, board, friend, notification, audit, report, and server-state collections. Many other collections are empty. These specimens cannot certify complete SP feature coverage, all enums, or empty-collection record schemas.

Custom-field numeric codes observed in the broad export are 0, 1, and 5. Their exact type-name mappings require SP documentation or code evidence; this analysis does not assign guessed labels.

Integer versus rank-string ordering and absent versus null values are version differences to retain explicitly. For example `customFields.order` is integer in the existing synthetic file but string in the broad export; `supportMarkdown` is null on migrated field definitions in the broad export.

## 7. Shared-feed to SP mapping review

| Shared-feed concept | Observed SP representation | Implementation status / decision |
| --- | --- | --- |
| One account | `users[]` with one owning profile; owned records use `uid` where applicable. | Direct structural mapping. Account identity/default generation rules still need agreement. |
| Member | One `members[]` record. | Direct mapping; retain identity across occurrences. |
| Group and nested Group | `groups[]`, `parent`, `members`. | Direct structural mapping. |
| System or Place anchor nested beneath another anchor | No distinct System/Place anchor collections or typed placement tree in these specimens. | Requires an approved projection, extension, or rejection policy. Never silently turn them into Groups. |
| Repeated member under Groups | Same member `_id` in multiple `groups[].members` arrays. | Representable. |
| Anchor relationships and user-defined labels | No corresponding typed relationship collection demonstrated. | Mapping/unsupported-feature behavior requires a decision. |
| Member note | `notes[]` with `member`, `title`, `note`, `date`. | Direct mapping; note defaults and missing dates require explicit generation rules. |
| Field definition and value | `customFields[]` and `members[].info[fieldId]`. | Direct for member fields; feed currently supplies labels/references but no value syntax. Anchor field values need a separate mapping decision. |
| Current front true | A live `frontHistory` row with start time and no endTime. | Timestamp/default rules required; do not use the host clock silently. |
| Current front false | No current row for that member. | Must reconcile with supplied history; detect contradictions. |
| Front-history event | Per-participant rows with `startTime`, optional `endTime`, `live`, `custom`. | Preserve the difference from PB multi-member events. |
| Visibility | `private`, `preventTrusted`, `buckets`, and default audience settings are observed. | Exact vocabulary mapping and inheritance must be settled. An empty bucket list is not proof of public visibility. |
| Operation permissions or account roles | No compatible definition established by these examples. | Do not map edit permissions to privacy buckets or token permission codes. |
| Arbitrary metadata/tags | No general extension contract demonstrated. | Do not invent SP keys and claim importer compatibility. |

The shared feed remains the objective. A second SP-only feed is not required by this evidence. Unsupported concepts should be reported precisely; their projection rules must be approved before a PB-shaped feed can be emitted as SP data.

## 8. Generated reference output

`simplyplural-synthetic-reference.json` is a new, deterministic reference fixture. It uses the 43 observed broad-export collection names with direct `_id` records. It populates the eight already-demonstrated synthetic collections using fictional Aurora data. Other collections remain empty; they are not presented as implemented features.

It contains:

- 1 synthetic user/system.
- 5 synthetic members, including an archived member.
- 6 Groups, including nested and empty-member Groups and repeated member associations.
- 2 custom fields with member values.
- 2 privacy buckets.
- 2 member notes.
- 1 custom front.
- 6 front-history rows: closed member rows, one closed custom-front row, and two concurrent current member rows.

The existing deleted-member reference is replaced with the existing synthetic archived member in this clean fixture. The row identifier and timing remain synthetic. A separate `simplyplural-edge-deleted-member.json` keeps the unresolved deleted-member reference as a labelled negative fixture. The supplied originals are untouched.

Owner `uid` references are added to the applicable synthetic records, following the broad specimen. No real names, descriptions, IDs, avatars, notes, credentials, access keys, tokens, security logs, or URLs are copied from the personal sources.

No privacy policy is inferred from bucket names. There is no claim that the generated file was accepted by the discontinued SP app: validation here proves JSON shape and the specified reference/timing invariants, not app-level compatibility.

This output is a reference dataset, not an implementation of the shared model-feed parser. Implementing the current feed requires resolving the System/Place projection, relationship mapping, permission/visibility definitions, and missing-value/default rules above. No files in Joshua’s repository have been modified by this analysis.

## 9. Verification

The accompanying `source-inventory.json` records source hashes, sizes, collection counts, observed field types/presence, generated counts, and validation results without personal record values.

Checks performed:

- Every generated root collection is an array and every generated record has a non-empty unique `_id` within its collection.
- User ownership, group parents/members, member field values, bucket references, note owners, and normal/custom front participants resolve.
- Group-parent traversal has no cycles.
- Front timestamps are integers; closed rows have end >= start; current rows omit endTime and use live true.
- The clean reference has zero validation errors.
- The negative fixture produces exactly one unknown front-history participant error.
- Rebuilding these artifacts produces byte-identical reference JSON.
- Source-file hashes remain unchanged.

No repository tests or actual application import were run: the current generator repository and running importer were not supplied with these four artifacts.

## 10. Cursor implementation boundary

Use this analysis and synthetic fixture as evidence when implementing `gen-simplyplural.py` behind `gen-import-engine.py`. Preserve `generate.py` and Joshua’s existing outputs. Do not replace the existing committed Simply Plural sample, because its deleted-member condition is meaningful test data.

Before adding a shared-feed serializer, settle the unresolved mappings. Then add independent tests for generated references, groups, duplicate placements, field values, note ownership, open/closed/custom fronts, privacy behavior, unsupported features, deterministic output, and preservation of existing outputs. Do not certify compatibility solely by comparing output with a fixture produced by the same code.

## 11. Feed-import proof of concept

`gen-simplyplural.py` maps `templates/model-feed-single.txt` through the shared engine. This is a proof of concept for that specimen, not a claim that the discontinued app accepted the file. `generate.py` and `docs/simplyplural/simplyplural-synthetic-reference.json` are unchanged.

Command and outputs:

```text
python gen-import-engine.py --model simplyplural --scriptfspec templates/model-feed-single.txt
```

- JSON: `out/imports/simplyplural/model-feed-single.json`
- PNGs: `out/imports/simplyplural/model-feed-single-avatars/<member _id>.png`

The PNG file name is `members[]._id`. `avatarUuid` on that same record is `synthetic-avatar-NNNN` with the same ordinal. No avatar URL is written. Members whose resolved avatar is `none` have neither field nor file.

Supported shape: one top-level System, Groups inside it, shared members, notes owned by one member, field definitions and member values, one privacy bucket, friends, and custom fronts. A second System, a Place, an anchor relationship, a Group custom-field association, or a note with no member is an error and does not replace output.

Defaults when the feed omits an SP field:

| Output | Value |
| --- | --- |
| Owning user `_id` and `uid` | `synthetic-system-0001` |
| `users[].username` | Account `name:` |
| `users[].desc` | The single System’s name |
| `users[].isAsystem` | `true` |
| Member `_id` and generated member `name` | `synthetic-member-0001` upward in first-seen order |
| Group `_id` | `synthetic-group-0001` upward. A Group directly under the System uses `parent` `root`. A nested Group uses its parent Group’s `_id`. |
| Note `title` | `""` |
| Note `supportMarkdown` | `false` |
| Note `date` and current front `startTime` | `1767225600000` (`2026-01-01T00:00:00Z`) |
| Custom field `type` | `0`, the text code used by the existing synthetic specimen. Other numeric codes are not named. |
| Custom field `order` | Definition order, starting at `0` |
| Field, note, bucket, and custom-front `_id` | The feed script id |
| Friend `_id` | `synthetic-friend-0001` |
| `frienduid` | `synthetic-frienduid-0001`, distinct from the friend `_id` and from the owning user |
| Omitted member color, pronouns, description, emoji, and group description | Omitted. They are not filled from the bucket name. |
| `seeMembers` and `seeFront` | Omitted. The feed does not supply them. |

Visibility uses both mechanisms from `src/api/v1/member.ts` in ApparyllisOrg/SimplyPluralApi release. The 1.11+ friend query matches bucket overlap and does not read the flags. The older field filter shows a trusted friend a private value only when `preventTrusted` is false, and shows friends a value when both flags are false.

- Account `self`, and members who do not override it, are `private: true` and `preventTrusted: true` with only buckets the feed listed.
- `trusted friends` is `private: true` and `preventTrusted: false`, plus those explicit buckets.
- Account `Permission: read` is printed as unmapped. It is not a bucket, role, or token code.
- Account email has no observed `users[]` field and is not written.
- A friend display name is `friends[].username` because that field is observed on a supplied friend specimen. The console summary also names the external `frienduid`. Alex is not a member and not a second `users[]` record.

`front: true` on a member writes one current `frontHistory` row: `custom: false`, `live: true`, the fixed `startTime`, and no `endTime`. `front: false` on a custom front writes the `frontStatuses` record only.


## Appendix A. Nested field-path inventory

These paths describe the direct-export and synthetic specimens. Dynamic identifiers are replaced by `<fieldId>`; API route counters are normalized. Types are observational, not a formal schema.

| JSON path | Observed types |
| --- | --- |
| `$.automatedReminders` | array |
| `$.avatarExports` | array |
| `$.avatarExports[]._id` | string |
| `$.avatarExports[].downloads` | integer |
| `$.avatarExports[].exp` | integer |
| `$.avatarExports[].key` | string |
| `$.avatarExports[].lastDownload` | integer |
| `$.avatarExports[].uid` | string |
| `$.boardMessages` | array |
| `$.boardMessages[]._id` | string |
| `$.boardMessages[].lastOperationTime` | integer |
| `$.boardMessages[].message` | string |
| `$.boardMessages[].read` | boolean |
| `$.boardMessages[].supportMarkdown` | boolean |
| `$.boardMessages[].title` | string |
| `$.boardMessages[].uid` | string |
| `$.boardMessages[].writtenAt` | integer |
| `$.boardMessages[].writtenBy` | string |
| `$.boardMessages[].writtenFor` | string |
| `$.cancelFeedback` | array |
| `$.channelCategories` | array |
| `$.channelCategories[]._id` | string |
| `$.channelCategories[].channels` | array |
| `$.channelCategories[].desc` | string |
| `$.channelCategories[].lastOperationTime` | integer |
| `$.channelCategories[].name` | string |
| `$.channelCategories[].uid` | string |
| `$.channels` | array |
| `$.channels[]._id` | string |
| `$.channels[].desc` | string |
| `$.channels[].lastOperationTime` | integer |
| `$.channels[].name` | string |
| `$.channels[].uid` | string |
| `$.chatMessages` | array |
| `$.chatMessages[]._id` | string |
| `$.chatMessages[].channel` | string |
| `$.chatMessages[].iv` | string |
| `$.chatMessages[].lastOperationTime` | integer |
| `$.chatMessages[].message` | string |
| `$.chatMessages[].uid` | string |
| `$.chatMessages[].writer` | string |
| `$.chatMessages[].writtenAt` | integer |
| `$.comments` | array |
| `$.customFields` | array |
| `$.customFields[]._id` | string |
| `$.customFields[].buckets` | array |
| `$.customFields[].name` | string |
| `$.customFields[].oid` | string |
| `$.customFields[].order` | integer, string |
| `$.customFields[].preventTrusted` | boolean |
| `$.customFields[].private` | boolean |
| `$.customFields[].supportMarkdown` | null |
| `$.customFields[].type` | integer |
| `$.customFields[].uid` | string |
| `$.dataExports` | array |
| `$.dataExports[]._id` | string |
| `$.dataExports[].downloads` | integer |
| `$.dataExports[].exp` | integer |
| `$.dataExports[].key` | string |
| `$.dataExports[].lastDownload` | integer |
| `$.dataExports[].uid` | string |
| `$.events` | array |
| `$.friends` | array |
| `$.friends[]._id` | string |
| `$.friends[].buckets` | array |
| `$.friends[].customFrontString` | string |
| `$.friends[].frienduid` | string |
| `$.friends[].frontNotificationString` | string |
| `$.friends[].frontString` | string |
| `$.friends[].getFrontNotif` | boolean |
| `$.friends[].getTheirFrontNotif` | boolean |
| `$.friends[].lastOperationTime` | integer |
| `$.friends[].seeFront` | boolean |
| `$.friends[].seeMembers` | boolean |
| `$.friends[].trusted` | boolean |
| `$.friends[].uid` | string |
| `$.frontHistory` | array |
| `$.frontHistory[]._id` | string |
| `$.frontHistory[].custom` | boolean |
| `$.frontHistory[].customStatus` | string |
| `$.frontHistory[].endTime` | integer |
| `$.frontHistory[].lastOperationTime` | integer |
| `$.frontHistory[].live` | boolean |
| `$.frontHistory[].member` | string |
| `$.frontHistory[].startTime` | integer |
| `$.frontHistory[].uid` | string |
| `$.frontStatuses` | array |
| `$.frontStatuses[]._id` | string |
| `$.frontStatuses[].avatarUrl` | string |
| `$.frontStatuses[].avatarUuid` | string |
| `$.frontStatuses[].buckets` | array |
| `$.frontStatuses[].color` | string |
| `$.frontStatuses[].desc` | string |
| `$.frontStatuses[].frame` | object |
| `$.frontStatuses[].frame.bgClip` | string |
| `$.frontStatuses[].frame.bgEndColor` | string |
| `$.frontStatuses[].frame.bgShape` | string |
| `$.frontStatuses[].frame.bgStartColor` | string |
| `$.frontStatuses[].lastOperationTime` | integer |
| `$.frontStatuses[].name` | string |
| `$.frontStatuses[].preventTrusted` | boolean |
| `$.frontStatuses[].preventsFrontNotifs` | boolean |
| `$.frontStatuses[].private` | boolean |
| `$.frontStatuses[].supportDescMarkdown` | boolean |
| `$.frontStatuses[].uid` | string |
| `$.fronters` | array |
| `$.groups` | array |
| `$.groups[]._id` | string |
| `$.groups[].buckets` | array |
| `$.groups[].color` | string |
| `$.groups[].desc` | string |
| `$.groups[].emoji` | string |
| `$.groups[].lastOperationTime` | integer |
| `$.groups[].members` | array |
| `$.groups[].name` | string |
| `$.groups[].parent` | string |
| `$.groups[].supportDescMarkdown` | boolean |
| `$.groups[].uid` | string |
| `$.invalidJwtTokens` | array |
| `$.members` | array |
| `$.members[]._id` | string |
| `$.members[].archived` | boolean |
| `$.members[].archivedReason` | string |
| `$.members[].avatarUrl` | string |
| `$.members[].avatarUuid` | string |
| `$.members[].buckets` | array |
| `$.members[].color` | string |
| `$.members[].desc` | string |
| `$.members[].frame` | object |
| `$.members[].frame.bgClip` | string |
| `$.members[].frame.bgEndColor` | string |
| `$.members[].frame.bgShape` | string |
| `$.members[].frame.bgStartColor` | string |
| `$.members[].info` | object |
| `$.members[].info.<fieldId>` | string |
| `$.members[].lastOperationTime` | integer |
| `$.members[].name` | string |
| `$.members[].pkId` | string |
| `$.members[].preventTrusted` | boolean |
| `$.members[].preventsFrontNotifs` | boolean |
| `$.members[].private` | boolean |
| `$.members[].pronouns` | string |
| `$.members[].receiveMessageBoardNotifs` | boolean |
| `$.members[].supportDescMarkdown` | boolean |
| `$.members[].uid` | string |
| `$.messages` | array |
| `$.notes` | array |
| `$.notes[]._id` | string |
| `$.notes[].color` | string |
| `$.notes[].date` | integer |
| `$.notes[].lastOperationTime` | integer |
| `$.notes[].member` | string |
| `$.notes[].note` | string |
| `$.notes[].supportMarkdown` | boolean |
| `$.notes[].title` | string |
| `$.notes[].uid` | string |
| `$.notifications` | array |
| `$.pendingFriendRequests` | array |
| `$.polls` | array |
| `$.potato` | array |
| `$.privacyBuckets` | array |
| `$.privacyBuckets[]._id` | string |
| `$.privacyBuckets[].color` | string |
| `$.privacyBuckets[].desc` | string |
| `$.privacyBuckets[].icon` | string |
| `$.privacyBuckets[].lastOperationTime` | integer |
| `$.privacyBuckets[].name` | string |
| `$.privacyBuckets[].rank` | string |
| `$.privacyBuckets[].uid` | string |
| `$.private` | array |
| `$.privateFront` | array |
| `$.privateFront[]._id` | string |
| `$.privateFront[].beforeCustomFrontString` | string |
| `$.privateFront[].beforeFrontNotificationString` | string |
| `$.privateFront[].customFrontString` | string |
| `$.privateFront[].customFronters` | array |
| `$.privateFront[].frontNotificationString` | string |
| `$.privateFront[].frontString` | string |
| `$.privateFront[].fronters` | array |
| `$.privateFront[].private` | boolean |
| `$.privateFront[].uid` | string |
| `$.private[]._id` | string |
| `$.private[].auditContentChanges` | boolean |
| `$.private[].auditRetention` | integer |
| `$.private[].categories` | array |
| `$.private[].defaultPrivacySettings` | object |
| `$.private[].defaultPrivacySettings.customFields` | array |
| `$.private[].defaultPrivacySettings.customFronts` | array |
| `$.private[].defaultPrivacySettings.groups` | array |
| `$.private[].defaultPrivacySettings.members` | array |
| `$.private[].generationsLeft` | integer |
| `$.private[].hideAudits` | boolean |
| `$.private[].lastExport` | integer |
| `$.private[].lastExportAttempt` | integer |
| `$.private[].lastGenerationReset` | integer |
| `$.private[].lastOperationTime` | integer |
| `$.private[].lastRefresh` | integer |
| `$.private[].latestVersion` | integer |
| `$.private[].location` | string |
| `$.private[].notificationHistory` | array |
| `$.private[].notificationHistory[].message` | string |
| `$.private[].notificationHistory[].timestamp` | integer |
| `$.private[].notificationHistory[].title` | string |
| `$.private[].notificationToken` | array |
| `$.private[].termsOfServiceAccepted` | boolean |
| `$.private[].termsOfServicesAccepted` | boolean |
| `$.private[].uid` | string |
| `$.queuedEvents` | array |
| `$.repeatedRemidners` | array |
| `$.repeatedReminders` | array |
| `$.reports` | array |
| `$.reports[]._id` | string |
| `$.reports[].createdAt` | integer |
| `$.reports[].uid` | string |
| `$.reports[].url` | string |
| `$.reports[].usedSettings` | object |
| `$.reports[].usedSettings.cc` | array |
| `$.reports[].usedSettings.customFronts` | object |
| `$.reports[].usedSettings.customFronts.buckets` | array |
| `$.reports[].usedSettings.customFronts.includeBucketless` | boolean |
| `$.reports[].usedSettings.customFronts.privacyLevel` | integer |
| `$.reports[].usedSettings.frontHistory` | object |
| `$.reports[].usedSettings.frontHistory.customFrontBuckets` | array |
| `$.reports[].usedSettings.frontHistory.end` | integer |
| `$.reports[].usedSettings.frontHistory.includeCustomFronts` | boolean |
| `$.reports[].usedSettings.frontHistory.includeCustomFrontsBucketless` | boolean |
| `$.reports[].usedSettings.frontHistory.includeMembers` | boolean |
| `$.reports[].usedSettings.frontHistory.includeMembersBucketless` | boolean |
| `$.reports[].usedSettings.frontHistory.memberBuckets` | array |
| `$.reports[].usedSettings.frontHistory.privacyLevel` | integer |
| `$.reports[].usedSettings.frontHistory.start` | integer |
| `$.reports[].usedSettings.members` | object |
| `$.reports[].usedSettings.members.buckets` | array |
| `$.reports[].usedSettings.members.includeBucketless` | boolean |
| `$.reports[].usedSettings.members.includeCustomFields` | boolean |
| `$.reports[].usedSettings.members.privacyLevel` | integer |
| `$.reports[].usedSettings.sendTo` | string |
| `$.securityLogs` | array |
| `$.securityLogs[]._id` | string |
| `$.securityLogs[].action` | string |
| `$.securityLogs[].at` | integer |
| `$.securityLogs[].ip` | string |
| `$.securityLogs[].uid` | string |
| `$.serverData` | array |
| `$.serverData[]._id` | string |
| `$.serverData[].lastReadMessage` | integer |
| `$.serverData[].migrated` | boolean |
| `$.serverData[].uid` | string |
| `$.sharedFront` | array |
| `$.sharedFront[]._id` | string |
| `$.sharedFront[].beforeCustomFrontString` | string |
| `$.sharedFront[].beforeFrontNotificationString` | string |
| `$.sharedFront[].customFrontString` | string |
| `$.sharedFront[].customFronters` | array |
| `$.sharedFront[].frontNotificationString` | string |
| `$.sharedFront[].frontString` | string |
| `$.sharedFront[].fronters` | array |
| `$.sharedFront[].uid` | string |
| `$.socketNotifications` | array |
| `$.subscribers` | array |
| `$.test` | array |
| `$.tokens` | array |
| `$.tokens[]._id` | string |
| `$.tokens[].permission` | integer |
| `$.tokens[].token` | string |
| `$.tokens[].uid` | string |
| `$.undeliveredMessages` | array |
| `$.usage` | array |
| `$.usage[].<method-and-route>` | integer |
| `$.usage[]._id` | string |
| `$.usage[].expireAt` | string |
| `$.usage[].uid` | string |
| `$.users` | array |
| `$.users[]._id` | string |
| `$.users[].avatarUrl` | string |
| `$.users[].color` | string |
| `$.users[].desc` | string |
| `$.users[].fields` | object |
| `$.users[].fields.<fieldId>` | object |
| `$.users[].fields.<fieldId>.name` | string |
| `$.users[].fields.<fieldId>.order` | integer |
| `$.users[].fields.<fieldId>.preventTrusted` | boolean |
| `$.users[].fields.<fieldId>.private` | boolean |
| `$.users[].fields.<fieldId>.type` | integer |
| `$.users[].frame` | object |
| `$.users[].isAsystem` | boolean |
| `$.users[].lastOperationTime` | integer |
| `$.users[].supportDescMarkdown` | boolean |
| `$.users[].uid` | string |
| `$.users[].username` | string |
| `$.verifiedKeys` | array |
| `$.views` | array |

## Appendix B. Source hashes

| Source | SHA-256 |
| --- | --- |
| `export_bVP6Jt40jqYWC2tfp54TZlg0sqq2.json` | `49549aba788170491927c962dc66a781389169966d12d9f188b6a60fc00ee5d2` |
| `simplyplural-official.json` | `33e63c9ab9dc617c88ff8a5e10698c4cf09c4f4e909cda30a727ae0e54578538` |
| `sp_export.zip` | `4d28e6d52c032e19af7ed95516830e563ad1974c2512aff07452aec7f7808091` |
| `sp.zip` | `9c9067108f6327608e97e6acd5bc013619516fc0f716f86df0f45a372abf0491` |
