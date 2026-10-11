# Ambulatoro pacientu pieraksta grafika optimizācija

Mazais praktiskais darbs kursā *Praktiskā kombinatoriālā optimizācija* (LU).

Katram pacientam jāpiešķir ārsts ar vajadzīgo specialitāti un vizītes sākuma laiks
tā, lai vizītes nepārklātos, un lai būtu minimālas novirzes no vēlamā laika,
ārstu dīkstāve, virsstundas un neieplānoti pacienti (svērti pēc steidzamības un vecuma).

## Struktūra

| Fails | Saturs |
|---|---|
| `scheduler/model.py` | domēns: ārsti, pacienti, risinājums |
| `scheduler/cost.py` | izmaksu funkcija (novērtēšana) |
| `scheduler/moves.py` | gājieni (SHIFT, REASSIGN, SWAP, UNASSIGN) + delta novērtēšana |
| `scheduler/construct.py` | sākotnējais risinājums (Decreasing + Cheapest Insertion) |
| `scheduler/sa.py` | Simulated Annealing un Hill Climbing |
| `scheduler/exact.py` | Branch & Bound optimuma iegūšanai mazajiem piemēriem |
| `scheduler/generate.py` | testa piemēru ģenerators |
| `instances/*.json` | 8 testa piemēri (6–300 pacienti, 2–25 ārsti) |
| `run_experiments.py` | visi eksperimenti → `results/` |
| `plots.py` | konverģences grafiks un grafika (Gantt) attēls |

## Palaišana

Nepieciešams Python 3.10+ (un `matplotlib` tikai attēliem).

```bash
python main.py instances/S1_5d_30p.json        # atrisināt vienu piemēru
python -m scheduler.generate                   # pārģenerēt testa piemērus
python run_experiments.py                      # visi eksperimenti (~15–20 min)
python plots.py                                # attēli
```
