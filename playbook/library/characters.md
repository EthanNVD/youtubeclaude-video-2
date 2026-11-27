# Characters — ready cast looks

A **character** asset is a saved cast entry: a preset + look fields + costume pieces. It lets the next film write
`"look": "malay_villager"` instead of repeating the colours and pieces.

## A complete character
```json
{"id": "malay_villager", "type": "characters", "name": "Malay villager (1940s)",
 "tags": ["malaya", "malay", "villager", "civilian", "kampong", "ww2"],
 "doc": "a Malay village man in a white baju, a songkok and a checked sarong",
 "spec": {"preset": "civilian_man", "color": "#e9e3cf", "skin": "#c8986c", "pants": "#3e5d8c", "age": 0.35, "wear": ["songkok", "sarong"]}}
```
Make it with `python tools/lib.py new characters malay_villager --project projects/<slug>`, then write the `spec`.

## Use it
```json
"cast": {"farmer": {"look": "malay_villager", "age": 0.6, "facial": "walrus"}}
```
The film's own fields win over the look's (here: older, with a moustache).

## Check
`lib preview --project … <id>`: the look standing and talking. `make.py … preview`: the whole cast.

## When to make one
When a kind of person will come back in other films (a Malay villager, a Sikh soldier, a Gurkha, an Australian
infantryman of 1942). Named people (Percival, Yamashita) stay in their film's cast.
