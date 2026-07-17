# ⚡ QUICKSTART — от `.txt` до гистограмм лага

Короткий сценарий запуска пайплайна JAVELIN-batch. Подробности про окружение,
Docker и X-сервер — в [README.md](README.md) / [readme-ru.md](readme-ru.md).

> **Только Python 2.7.** Все команды запускайте через `python2` (этого требует
> JAVELIN v0.33). Все скрипты пайплайна запускаются **из папки `scripts/`**.

---

## 0. Подготовьте входные данные

Положите сырые кривые блеска в `../light_curves/` рядом с папкой `scripts/`:

```text
object1/
 ├── scripts/            <-- вы здесь
 └── light_curves/
      ├── my_obj_cont.txt   <-- континуум (суффикс _cont)
      └── my_obj_line.txt   <-- линия     (суффикс _line)
```

Требования к `.txt`:
- **3 колонки:** MJD, поток/звёздная величина, ошибка (пробел/таб).
- Строки, начинающиеся с `#`, игнорируются.
- В имени файла обязателен суффикс **`_cont`** (континуум) или **`_line`** (линия) —
  по ним работают шаблоны поиска в конфигах.

Нет своих данных? Сгенерируйте тестовые:

```bash
cd utilities
python2 lc_gen.py        # создаёт ../../light_curves/simulated_{cont,line}.txt
python2 lc_plot.py       # (опц.) сохраняет ../../light_curves/light_curves.png
cd ..
```

---

## 1. Подготовка (`preparation.py`)

```bash
python2 preparation.py
```

Создаёт структуру папок (`jav_data`, `results`, `_sessions`, `_versions`),
чистит `.txt` → `.dat` в `../jav_data/`, и пишет дефолтный конфиг
`../light_curves/start1.cfg`.

---

## 2. Настройте MCMC (`start1.cfg`)

Откройте `../light_curves/start1.cfg`. Для нескольких прогонов копируйте файл
(`runA.cfg`, `runB.cfg`) — `run_javelin.py` обработает **все** `*.cfg`.

```ini
[paths]
cont_pattern = ../jav_data/*_cont*.dat
line_pattern = ../jav_data/*_line*.dat
chains_path  = ../jav_data/chains_run1/
log_path     = ../jav_data/logs/run1.log

[mcmc]
n_walkers     = 100
n_burn        = 500
n_chain       = 500
lag_limit_min = 0
lag_limit_max = 10
n_iter        = 50      # число выходных файлов цепей (.jav)
```

> ⚠️ Для разных `.cfg` задавайте **разные** `chains_path` и `log_path`, иначе
> новый прогон перезапишет результаты предыдущего.

---

## 3. Запуск вычислений (`run_javelin.py`)

```bash
python2 run_javelin.py
```

Найдёт все `.cfg`, прогонит по очереди, покажет прогресс-бар; подробный вывод
JAVELIN уйдёт в `.log`. Результат — папка `chains_run1/` с файлами `.jav`.

---

## 4. Подбор вида гистограммы (GUI, `hist_tuner.py`)

> Требуется X-дисплей (см. README про Docker + VcXsrv/Xming).

```bash
python2 hist_tuner.py
```

1. `Open chain` → выберите один репрезентативный `.jav`.
2. `column = 3` (колонка лага), настройте `x_min/x_max`, `bins`, `lag_peak`.
3. `Plot hist` — предпросмотр; закройте, поправьте, повторите.
4. Цвета: `hist_color` (напр. `#601fb4`), `line_color` (напр. `#ff0000`).
5. `Save config` — настройки и цвета пишутся в `hist.ini`.

Предпросмотр и пакетный экспорт используют общий модуль `histlib.py`, поэтому
картинки из шага 5 будут точно такими же, как в предпросмотре.

---

## 5. Пакетный экспорт PNG (`chains2hist.py`)

```bash
python2 chains2hist.py
```

Читает `hist.ini`, находит все `.jav`, сортирует натурально (1, 2 … 10) и
сохраняет `.png` в `output_dir` (по умолчанию `../results/run1/`). Работает без
GUI/X-дисплея.

---

## 🛠 Частые ошибки

| Симптом | Что делать |
|---|---|
| `No module named ConfigParser` / синтаксис | Запускайте через `python2`, не `python3`. |
| `No files found matching pattern...` | Проверьте `cont_pattern`/`line_pattern` в `.cfg` (шаг 3) или `data_dir`/`file_pattern` в `hist.ini` (шаг 5). |
| `could not convert string to float` | В поле GUI неверный символ; десятичный разделитель — точка (`3.5`, не `3,5`). |
| Окно GUI не открывается (Docker) | Запущен ли VcXsrv/Xming и правильный ли `DISPLAY`? См. README. |
| Папки пишутся не туда | Скрипты пайплайна используют относительные пути — запускайте из `scripts/`. |
