#! /usr/bin/env bash

# Go to script dir
cd "${0%/*}"
DIR=$(pwd)

NAME=$(basename $(dirname $DIR))
API=$(grep "X-Plasma-API" ../metadata.desktop | sed 's/.*=//')
case "$API" in
  "python") SCRIPTEXT="py" ;;
  "ruby-script") SCRIPTEXT="rb" ;;
  "webkit") SCRIPTEXT="js" ;;
  * ) exit ;;
esac

VERSION=$(grep "X-KDE-PluginInfo-Version" ../metadata.desktop | sed 's/.*=//')

XGETTEXT="xgettext --from-code=UTF-8 -kde -ci18n -ki18n:1 -ki18nc:1c,2 -ki18np:1,2 \
          -ki18ncp:1c,2,3 -ktr2i18n:1 -kI18N_NOOP:1 -kI18N_NOOP2:1c,2 -kaliasLocale \
          -kki18n:1 -kki18nc:1c,2 -kki18np:1,2 -kki18ncp:1c,2,3xgettext -ki18n -ki18nc
          -ki18ncp -ki18np"
EXTRACTRC="extractrc"

if [ "x$1" != "x" ]; then
    if [ ! -d "locale/$1" ]; then
        mkdir -p "locale/$1/LC_MESSAGES"
    fi
fi

$EXTRACTRC ui/*.ui config/*.xml > ./rc.$SCRIPTEXT
$XGETTEXT rc.$SCRIPTEXT code/*.$SCRIPTEXT -o "$NAME.pot"
sed -e 's/charset=CHARSET/charset=UTF-8/g' -i "$NAME.pot"
sed -e 's/SOME DESCRIPTIVE TITLE./gmail-plasmoid language translation file./g' -i "$NAME.pot"
sed -e "s/Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER/Copyright (C) 2009 Mark McCans/g" -i "$NAME.pot"
sed -e 's/This file is distributed under the same license as the PACKAGE package./This file is distributed under the same license as the gmail-plasmoid package./g' -i "$NAME.pot"
sed -e 's/FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.//g' -i "$NAME.pot"
sed -e "s/Project-Id-Version: PACKAGE VERSION/Project-Id-Version: $VERSION/g" -i "$NAME.pot"

for d in locale/*; do
    if [ -d "$d" ]; then
        if [ -f "$d/LC_MESSAGES/$NAME.po" ]; then
            echo "Merging $NAME.pot -> $d/LC_MESSAGES/$NAME.po ..."
            msgmerge -U "$d/LC_MESSAGES/$NAME.po" "$NAME.pot"
        else
            echo "Copying $NAME.pot -> $d/LC_MESSAGES/$NAME.po ..."
            cp "$NAME.pot" "$d/LC_MESSAGES/$NAME.po"
        fi
    fi
done

for d in locale/*; do
    echo "Making $d/LC_MESSAGES/$NAME.mo ..."
    msgfmt "$d/LC_MESSAGES/$NAME.po" -o "$d/LC_MESSAGES/$NAME.mo"
done

rm -f rc.$SCRIPTEXT
#rm -f $NAME.pot
