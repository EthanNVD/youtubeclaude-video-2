# Understanding — malaya-test (a 66 s cut of fall-of-singapore, 09:36–10:42)

The worked example of the living library: every person, costume, plant, building and place below was either found in the
library, adapted from it, or made for this film and then promoted (playbook/library.md).

## 1. The film in three lines
- **Question**: how did the Japanese army move so fast through Malaya?
- **Answer / verdict**: by bicycle along roads and plantations, not through the jungle; the "impassable jungle" is a myth.
- **Era and sides**: WW2, Malaya December 1941 – January 1942; Japan vs the British Commonwealth (British, Indian, Australian).

## 2. People (nobody is named in this cut)

| cast id | preset | name on the name card | role on the name card | what they do in the story |
|---|---|---|---|---|
| jp_officer | japanese_officer + jp_field_cap | — | — | lands at Singora with a practical idea, counts the one bicycle |
| jp_soldier (2, 3) | japanese_soldier + jp_field_cap | — | — | take bicycles, ride south three abreast, laugh, file past roadblocks |
| shopkeeper | civilian_man + singlet (bare arms) | — | — | Chinese shopkeeper whose bicycle is taken |
| villager (2), villager_woman | civilian_man/woman + songkok + sarong | — | — | Malay villagers cycling, walking in the kampong |
| tapper | civilian_man + singlet + white sarong (recoloured) | — | — | Tamil rubber tapper cutting a tree |
| brit_officer | british_soldier, beard, jungle green | — | — | lies hidden in the grass beside the road and watches |
| staff1, staff2 | british_soldier, khaki drill, peaked cap | — | — | Malaya Command staff sure that the jungle is impassable |
| aus_soldier (2) | british_soldier + slouch_hat | — | — | look at the jungle wall; dig in too late |
| sikh_soldier, brit_soldier | british_soldier + sikh_turban / helmet_uk | — | — | hold a roadblock while the Japanese go round it |
| host | host | — | — | presents the first myth at the gate |

## 3. Story arcs
| arc | person(s) | main place(s) | where it starts and where it returns |
|---|---|---|---|
| bicycles | jp_officer, jp soldiers, shopkeeper | singora_beach, malay_town, estate_road | the beach → the town → the road south |
| the hidden watcher | brit_officer | estate_road | lies hidden → watches the riders pass |
| the jungle myth | staff1, aus_soldier, jp_soldier | hq_office, jungle_myth, rainforest_edge | the myth → the truth (plantations) → the jungle edge |

## 4. Story places
| place_id | setting | tag text | appears at | changes |
|---|---|---|---|---|
| singora_beach | compose: sea, sand, coconut palms | Singora, Thailand · 8 December 1941 | 0:00, 0:04 | dawn |
| malay_town | compose: hills, laterite road, shophouse row, palms | A Malayan town · December 1941 | 0:06, 0:08 | haze |
| estate_road / estate_road_open | compose: rubber rows, laterite road (± lalang in front) | Behind the Japanese lines · January 1942 | 0:10–0:26, 0:57 | haze |
| rubber_estate, kampong, rainforest_edge, jungle_myth, roadblock | compose | (see cards/_film.json) | 0:34–1:06 | haze; fog for the myth |
| hq_office | room office: map, window, flag UK, clock | Malaya Command, Singapore · 1941 | 0:30, 0:37 | — |
| host_study | room parlour | — | 0:26 | — |

## 5. Symbols and big questions
- **Symbols**: the bicycle (speed), the wall of jungle (the myth), the gate ledger (the film's device).
- **Big questions**: none in this cut.

## 6. Numbers
- "groups of 40 or 50, 3 or 4 abreast": spoken only; the picture shows rows three abreast, many rows.

## 7. Chapters
| # | starts at | title | what happens | arcs / places |
|---|---|---|---|---|
| 1 | 0:00 The Japanese army also | Bicycles and the jungle | bicycles, the hidden watcher, the jungle myth and the truth | all |

## 8. Beats
```
0:00 | The Japanese army also | jp_officer + soldiers | come ashore, the officer taps his temple | singora_beach | dawn | scene
0:04 | It did not bring       | officer, one rider     | counts one finger, shrugs at the one bicycle | singora_beach | dawn | scene
0:06 | It knew Malaya was     | villagers, shopkeeper  | ride bicycles past the shophouses | malay_town | haze | scene (cyclists)
0:08 | so it took them        | soldier, shopkeeper    | soldier rides off on the shop's bicycle, shopkeeper protests | malay_town | haze | scene
0:10 | and rode south         | Japanese cyclists      | ride left (south) three abreast | estate_road_open | haze | scene (cyclists)
0:12 | A British officer who  | brit_officer           | lies in the lalang with binoculars | estate_road | haze | scene, letterbox
0:16 | later described them  | officer + cyclists     | over his shoulder, rows of riders pass | estate_road | haze | scene (cyclists)
0:22 | chatting and laughing  | cyclists               | chat and laugh as they pedal | estate_road_open | haze | scene (cyclists)
0:26 | which brings us to     | host                   | shows the gate ledger: myth No. 1 | host_study | — | scene + paper_note
0:30 | You'll often hear that | staff1, staff2         | point at the map, "nobody comes through" | hq_office | — | scene
0:34 | so the Japanese simply | soldiers               | walk through a misty jungle (sepia, MYTH stamp) | jungle_myth | fog | scene
0:37 | The truth is more      | staff1                 | scratches his head | hq_office | — | scene (close)
0:39 | Much of what everyone  | tapper                 | taps a rubber tree | rubber_estate | haze | scene
0:43 | coconut groves         | villagers              | walk and cycle through the kampong | kampong | haze | scene
0:46 | The real jungle at     | aus_soldier            | looks up at the jungle wall, turns back | jungle_edge | haze | scene
0:49 | and the Australian     | —                      | the official history's words | — | — | document (book)
0:54 | The Japanese mostly    | jp_soldier             | lifts his parang, shakes his head | jungle_edge | haze | scene
0:57 | They used the roads    | cyclists + a file      | ride the road, walk through the rubber | estate_road_open | haze | scene
1:00 | went around the        | sikh + brit soldiers   | aim down the road while the Japanese file past behind | roadblock | haze | scene
1:03 | and kept moving        | aus soldiers           | dig while cyclists stream past | roadblock | haze | scene
```

## 8b. Pre-production — what the pictures need

| kind | id | description | first used at |
|---|---|---|---|
| costume | jp_field_cap | Japanese field cap with neck flaps, star | 0:00 |
| costume | songkok | Malay black velvet cap | 0:06 |
| costume | sarong | checked sarong (recoloured per person) | 0:06 |
| costume | singlet | white singlet neckline (bare arms via armColor) | 0:06 |
| costume | sikh_turban | Sikh khaki turban (Indian Army) | 1:00 |
| costume | slouch_hat | Australian slouch hat, brim up | 0:46 |
| vehicle | bicycle | bicycle people ride (library, now with anchors seat/crank and rolling wheels) | 0:04 |
| plant | rubber_tree | tapped rubber tree with latex cup, in rows | 0:10 |
| plant | coconut_palm | coconut palm with swaying crown | 0:00 |
| plant | jungle_edge | dense rainforest wall | 0:34 |
| plant | banana_plant | banana plant | 0:43 |
| plant | lalang_grass | tall grass clump that hides a watcher | 0:12 |
| building | kampong_house | Malay house on stilts | 0:43 |
| building | shophouse | Chinese shophouse with five-foot way | 0:06 |
| prop | parang | Malay machete, held | 0:54 |
| prop | sandbag_wall | low sandbag wall (roadblock) | 1:00 |
| place | estate_road | compose: rubber rows, laterite road, lalang | 0:10 |

## 9. Fact flags
- The narration says "passable" at 0:32; the myth is that the British thought the jungle **impassable**. Nothing on screen says either word.
- Singora (Songkhla) is in Thailand: the tag says so.
