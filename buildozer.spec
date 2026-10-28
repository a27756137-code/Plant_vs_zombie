[app]

# (str) Название твоей приложения (отображается на телефоне)
title = Plants vs Zombies Ultimate

# (str) Имя пакета без пробелов и заглавных букв
package.name = pvzultimate

# (str) Домен пакета
package.domain = org.pvz

# (str) Путь к исходным файлам игры (относительно папки с buildozer.spec)
# '.' означает текущая папка, где лежат main.py и pvz_save.json (если есть)
source.dir = .

# (list) Какие расширения файлов включать в APK
source.include_exts = py,png,jpg,atlas,json,wav,ogg

# (list) Список файлов, которые нужно исключить (пусто)
source.exclude_exts = 

# (list) Папки, которые нужно исключить из сборки
source.exclude_dirs = tests, bin, .git, __pycache__

# (str) Версия приложения
version = 1.0

# (list) Зависимости приложения. 
# Обязательно нужны python3 и pygame.
requirements = python3,pygame

# (str) Поддерживаемые языки (необязательно)
# orientation = landscape — критически важно, так как наша игра горизонтальная!
orientation = landscape

# (bool) Указывать ли флаг полноэкранного режима
fullscreen = 1

# (list) Разрешения для Android (INTERNET нужен, если планируешь добавить сетевые функции)
android.permissions = INTERNET

# (int) Целевой уровень API Android (желательно ставить не ниже 31-33 для современных телефонов)
android.api = 33

# (int) Минимальная версия Android, на которой запустится игра (21 = Android 5.0 Lollipop)
android.minapi = 21

# (int) Версия Android SDK, используемая для сборки
android.sdk = 33

# (str) Версия Android NDK для компиляции C/C++ частей Pygame
android.ndk = 25b

# (list) Архитектуры процессоров телефона. 
# arm64-v8a и armeabi-v7a покрывают практически 99% современных смартфонов на Android.
android.archs = arm64-v8a, armeabi-v7a

# (bool) Автоматически принимать лицензии Android SDK при сборке
android.accept_sdk_license = 1


[buildozer]

# (int) Уровень логирования (0 = ошибки, 1 = варнинги, 2 = полный лог сборки)
log_level = 2

# (int) Предупреждение при попытке запустить сборку от суперпользователя (root)
warn_on_root = 1

# (str) Путь для сохранения скомпилированных файлов (по умолчанию папка .buildozer)
# build_dir = .buildozer

# (str) Папка, куда будет складываться готовый .apk файл
bin_dir = ./bin
