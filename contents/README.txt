This document contains brief instructions on how to create new translations for
the gmail-plasmoid widget. If any of the instructions are unclear or you
encounter any difficulties please contact the author at the following email
address:

Mark McCans <mjmccans+gmail-plasmoid@gmail.com>


---------------------------------------------
Step 1: Creating a new gmail-plasmoid.po file
---------------------------------------------
First, under the "locale" folder create a new sub-folder with the same name as your locale, and create a further sub-folder named "LC_MASSAGES". For example, for a French translation you would create the following folders "locale/fr/LC_MESSAGES". Second, copy the gmail-plasmoid.pot file from the "contents" directory into your new LC_MESSAGES directory and rename it gmail-plasmoid.po (in other words, change the extension from .pot to .po). You are now ready to start translating.

--------------------------------------
Step 2: Translate the required strings
--------------------------------------
While you can edit the gmail-plasmoid.po file in any text editor, using the
“lokalize” program can make your life easier. This program is packaged for most
distributions so it should be easy to install. Whatever method you choose, you
need to supply a translation for all of the strings that appear in the .po file.

If you encounter any strings that you cannot translate due to the choice of
words or some other issue, please contact the author to work out a solution.

-------------------------------------------
Step 3: Convert the .po file to an .mo file
-------------------------------------------
In order for the widget to use a translation it must be converted to an .mo
file. This is done using the "Messages.sh" script found in the "contents" folder, which creates updated .mo files for all translations.

----------------------------------------------------------
Step 4: Send the translation for inclusion with the widget
----------------------------------------------------------
Once you are happy with the translation please send the .po file to the author
along with translations for the following three strings:

For the notification configuration screen:
   “New Mail Arrived”
   “No Unread Mail”

For the “add widgets” screen:
   “Check one or more Gmail accounts”

When you send the .po file and the three strings above, please indicate whether
you give permission to the author to include your name in the THANKS file.


