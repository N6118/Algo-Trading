# This file must be used with "source bin/activate.csh" *from csh*.
# You cannot run it directly.
<<<<<<< HEAD
=======

>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa
# Created by Davide Di Blasi <davidedb@gmail.com>.
# Ported to Python 3.3 venv by Andrew Svetlov <andrew.svetlov@gmail.com>

alias deactivate 'test $?_OLD_VIRTUAL_PATH != 0 && setenv PATH "$_OLD_VIRTUAL_PATH" && unset _OLD_VIRTUAL_PATH; rehash; test $?_OLD_VIRTUAL_PROMPT != 0 && set prompt="$_OLD_VIRTUAL_PROMPT" && unset _OLD_VIRTUAL_PROMPT; unsetenv VIRTUAL_ENV; unsetenv VIRTUAL_ENV_PROMPT; test "\!:*" != "nondestructive" && unalias deactivate'

# Unset irrelevant variables.
deactivate nondestructive

<<<<<<< HEAD
setenv VIRTUAL_ENV "/Users/na61/Desktop/US stockmarket Algotrading /algo-trade-platform/venv"

set _OLD_VIRTUAL_PATH="$PATH"
setenv PATH "$VIRTUAL_ENV/bin:$PATH"
=======
setenv VIRTUAL_ENV /home/anurag/Desktop/Algo-Trading/algo-trade-platform/venv

set _OLD_VIRTUAL_PATH="$PATH"
setenv PATH "$VIRTUAL_ENV/"bin":$PATH"
>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa


set _OLD_VIRTUAL_PROMPT="$prompt"

if (! "$?VIRTUAL_ENV_DISABLE_PROMPT") then
<<<<<<< HEAD
    set prompt = "(venv) $prompt"
    setenv VIRTUAL_ENV_PROMPT "(venv) "
=======
    set prompt = '(venv) '"$prompt"
    setenv VIRTUAL_ENV_PROMPT '(venv) '
>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa
endif

alias pydoc python -m pydoc

rehash
