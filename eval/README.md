# Evaluation
## Eval for both Linux and Windows
### Windows eval files all contain win in their name
#### For Windows, usage order is win_performance_eval, aggregate_win, plot_win


## Existing evals
python3 win_performance_eval.py
Add -r <int> for number of runs
### Clear-Obfus
#### -e clear -o
### Different client numbers
#### -c 1 ... -c 5
### Downlevel and reducing encrypted message size
#### -l 5 -z
### Obfuscation
#### -o
### Obfuscation and reducing encrypted message size
#### -o -z
### Synthetic evals 10 to 100
#### -s <Min/Abs/Add>