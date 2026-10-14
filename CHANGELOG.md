## [v1.1.0] — 2026-10-14 (Bug Fix Release)
### Исправлено
* **Завершение процессов `language_server*.exe`:** `IDE_PROCESS_NAMES` дополнен исполняемыми файлами языкового сервера (`language_server_windows_x64.exe`, `language_server_windows_arm64.exe`, `language_server.exe`), что предотвращает блокировку файлов при патчинге.
* **Полная очистка при удалении (`remove_ai_bypass`):** Удаляется не только `settings-backup`, но и каталог `%LOCALAPPDATA%\AIBypass\doh\` (включая логи, PID и состояние маршрутов).
* **Синхронизация DoH-эндпоинтов:** Приведён к единому виду перечень эндпоинтов (`dns.dns-ai.ru/dns-query`, `dns-ai.ru/dns-query`, `dns.comss.one/dns-query`).
* **Утечка сокетов в `query_geohide_dns`:** сокет теперь закрывается в `finally`-блоке независимо от исхода запроса.
* **`doh_server_running` давал false positive:** функция теперь сначала проверяет PID-файл и живость процесса через `tasklist`, и только затем делает UDP-probe. Чужой процесс на порту 53 (Docker, AdGuard) больше не воспринимается как наш форвардер.
* **Кэш результата `doh_server_running`:** результат кэшируется на 1.5 сек, чтобы `tasklist` не запускался на каждую перерисовку меню. Места где нужен живой ответ (`doh_server_start`, `doh_server_stop`) передают `max_age=0`.
* **hosts-блок вставлялся в начало файла:** `write_cloudcode_hosts` теперь добавляет блок `# BEGIN/END AI-Bypass-CloudCode` в конец `hosts`, системные записи (`127.0.0.1 localhost` и др.) остаются на своих местах.
* **`/32` маршруты добавлялись при неудачной записи hosts:** `add_host_routes` теперь вызывается только если `write_cloudcode_hosts` успешно отработал.
* **JSONC-комментарии в `settings.json`:** regex для замены `jetski.cloudCodeUrl` теперь пропускает строки, начинающиеся с `//`. Если ключ присутствовал только в комментарии — файл не изменялся (раньше значение записывалось прямо внутрь комментария).
* **AAAA-ответы теперь кэшируются:** `_handle_doh_query` кэширует ответы не только для A-записей (qtype 1), но и для AAAA (qtype 28).
## [v1.0.0] — 2026-10-12 (Unified Python Edition — Stable)
### Добавлено
* **Единая кнопка установки и удаления (One-button install / remove):** Убраны отдельные пункты для браузеров и Antigravity. Теперь `[1] Install AI Bypass` ставит всё сразу — NRPT, патч `language_server`, hosts-пин для Cloud Code, autostart. Пункт `[3] Remove AI Bypass` делает полный откат одной операцией.
* **Локальный DoH-форвардер с fallback (RFC 8484):** Собственный DNS-сервер на `127.0.0.1:53` умеет отвечать по RFC 8484 (POST `application/dns-message`), кэширует ответы по min TTL, а при отказе DoH-эндпоинтов переключается на прямой UDP. Автозапуск через Task Scheduler на `ONLOGON /RL HIGHEST` — сервис живёт после перезагрузки без ручного вмешательства.
* **Автовосстановление форвардера:** При старте меню `ensure_forwarder_if_needed()` проверяет, указывает ли NRPT на loopback, и если да, а сервис мёртв — поднимает его автоматически. Плюс самолечение UDP-сокета от ICMP port-unreachable через `WSAIoctl(SIO_UDP_CONNRESET)` — форвардер больше не падает при закрытых клиентских портах.
* **Обнаружение прямых substituters (Direct substituter discovery):** Установка сама опрашивает Comss и Geohide по UDP и находит NS, которые реально возвращают non-Google A-записи для `gemini.google.com`, `aistudio.google.com`, `generativelanguage.googleapis.com`. NRPT для Gemini/Antigravity API теперь ставится на эти прямые NS — DoH-форвардер нужен только как резерв.
* **Объединённое NRPT-правило для Google AI (Unified Google AI NRPT rule):** Один `AI-Bypass-DoH` для всех Gemini + Antigravity API доменов вместо двух пересекающихся правил. Устранён конфликт namespace `generativelanguage.googleapis.com`.
* **SNI-pinning Cloud Code (geohide discovery + hosts + /32 routes):** Для `daily-cloudcode-pa.googleapis.com` установка опрашивает geohide DNS, TLS-пробует полученные non-Google адреса с SNI хоста, пиннит рабочий IP в `hosts`, добавляет `/32` маршрут через физический интерфейс. Это обходит региональный отказ `User location is not supported` без VPN.
* **NODATA для AAAA/SVCB/HTTPS на Google-доменах:** Форвардер возвращает NOERROR/NODATA на IPv6-запросы к подставленным фронтендам (они IPv4-only). Убирает залипание браузера на Happy-Eyeballs IPv6.
* **Готовность к состоянию "нет DoH":** Все три публичных DoH-эндпоинта `dns-ai.ru` / `dns-ai.ru/dns-query` / `dns.comss.one` сейчас могут быть недоступны (404, SSL mismatch). Установка не ломается: Gemini/Antigravity работают через прямые NS, а форвардер остаётся как страховка.

### Изменено
* **`print_status()`:** Показывает реальную цель NRPT — `direct NS: <IP1>, <IP2> ...` или `DoH forwarder`, вместо жёсткого `DoH dns-ai.ru`. Убрано ложное `[BROKEN]` при прямых NS. Добавлено `autostart: on / off`.
* **`show_details()`:** Живая диагностика — `Cloud Code geohide discovery`, `Gemini substituter (live)`, `DoH endpoints (live probe)` с фактическими адресами и статусами. Сразу видно, что работает, а что нет.
* **`_safe_write_hosts()`:** Двухступенчатая запись — сначала атомарная замена через `os.replace`, при отказе Windows (DNS Client / Defender / read-only) — in-place overwrite с предварительным снятием флага read-only. Логирование обеих попыток в `server.log`.
* **Сообщение об ошибке записи hosts:** Теперь явно указывает путь и файл лога для диагностики.

### Удалено
* **Отдельные пункты меню:** `Enable Browser Bypass`, `Switch SmartDNS`, `Google Antigravity` — заменены единым `Install / Remove AI Bypass`.
* **Двойной NRPT для Gemini/Antigravity:** Убрано разделение на `GEMINI_DOMAINS` и `ANTIGRAVITY_DOMAINS` при применении — список объединяется в один `google_domains` и получает одно правило.
* **Старый CLI-подход `antigravity-bypass-russia.exe` из v0.1.1:** Полностью заменён встроенным Python-движком (патч `language_server` x64/ARM64, `settings.json`, `CLOUDB_CODE_URL`, V8 cache).

### Исправлено
* **Преждевременный выход форвардера (`DoH forwarder down` через 6 минут):** ICMP port-unreachable от закрытых клиентских портов через `SIO_UDP_CONNRESET`; ошибки `recvfrom` больше не завершают процесс.
* **Ложное отсутствие подстановки для Gemini:** Direct substituter discovery вместо доверия одному DoH-эндпоинту.
* **Преждевременный региональный отказ Antigravity:** SNI-пин geohide-DNS + hosts + `/32` route вместо надежды на DNS-подстановку для Cloud Code.
* **Потеря Cloud Code после ребута:** Task Scheduler `ONLOGON` + `ensure_forwarder_if_needed()` при старте меню.

### Известные ограничения
* DoH-эндпоинт `dns.dns-ai.ru/dns-query` отвечает `HTTP 404` с 12.10.2026; `dns.comss.one/dns-query` — сертификат не соответствует хосту. Форвардер в этом состоянии работает как UDP-прокси с geohide-приоритетом для Google-доменов.
* `cloudcode-pa.googleapis.com` (без `daily-`) не пиннится — geohide для него возвращает реальные Google IP. Это не критично, поскольку `settings.json` направляет IDE именно на `daily-`.
* На чистых системах возможны конфликты с `SharedAccess` (ICS) или Docker Desktop за порт `127.0.0.1:53` — тогда форвардер упадёт с `FATAL bind`, а NRPT продолжит работать через прямые NS.