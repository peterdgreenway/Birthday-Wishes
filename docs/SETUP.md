# Birthday Wishes — Setup

Colourful **Vestaboard Note** (15×3) that says **Happy Birthday** for people you configure.

## Enable

1. **Integrations** → **Birthday Wishes**
2. Enter the **Birthdays list** (one person per line)
3. Choose **Display mode**
4. **Save Changes**

## Import from a text file

1. Create a file on the **FiestaBoard host**, e.g. `/data/birthdays.txt`
2. Use this format (**one person per line**):

```
Alice Smith, 15/03
Bob Jones, 22/06
Carol White, 25/12
```

3. In **Integrations → Birthday Wishes**, set **Import from text file (path)** to that path  
4. **Save Changes**

If the file is readable, it **overrides** the Birthdays list box.  
A sample file is in the plugin repo: `examples/birthdays.txt`.

## Birthdays list format

```
Alice Smith, 15/03
Bob Jones, 1990-06-22
Carol, 3-15
Dave Brown | 25 December
```

- **Day/month** preferred as `DD/MM` (UK style)
- Year is optional
- Lines starting with `#` are ignored

## Note page

```
{{birthday_wishes.note_row1}}
{{birthday_wishes.note_row2}}
{{birthday_wishes.note_row3}}
```

Example:

```
{65}{68} HAPPY
BIRTHDAY
    ALICE
```

## Happy Birthday block

```
{{birthday_wishes.happy_block}}
```

→ `Happy Birthday Alice`

Or three Note rows:

```
{{birthday_wishes.happy_row1}}
{{birthday_wishes.happy_row2}}
{{birthday_wishes.happy_row3}}
```

## Separate fields

| Variable | Example |
|----------|---------|
| `forename` | Alice |
| `surname` | Smith |
| `full_name` | Alice Smith |
| `day` | 15 |
| `month` | 3 |
| `month_name` | March |

## Display modes

| Mode | Behaviour |
|------|-----------|
| **today_or_next** (default) | Today’s birthday, or the next upcoming one |
| **today_only** | Only shows when it is someone’s birthday |

## Install from GitHub

```bash
curl -X POST http://localhost:4420/api/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"repository": "https://github.com/peterdgreenway/fiestaboard-plugin--birthday-wishes"}'
```
