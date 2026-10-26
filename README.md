# FiestaBoard plugin: Birthday Wishes

Happy Birthday messages on a **Vestaboard Note** (15×3) for multiple people, with themed colour tiles.

## Note layout

```
{{birthday_wishes.note_row1}}
{{birthday_wishes.note_row2}}
{{birthday_wishes.note_row3}}
```

```
{65}{68} HAPPY
BIRTHDAY
    ALICE
```

## Happy Birthday block

`{{birthday_wishes.happy_block}}` → `Happy Birthday Alice`

## Component variables

`forename`, `surname`, `day`, `month`, `month_name`, `full_name`

## Install

```bash
curl -X POST http://localhost:4420/api/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"repository": "https://github.com/peterdgreenway/fiestaboard-plugin--birthday-wishes"}'
```

Plugin id: `birthday_wishes`  
Author: **peterdgreenway**

## Licence

MIT
