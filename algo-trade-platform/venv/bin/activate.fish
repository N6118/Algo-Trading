# This file must be used with "source <venv>/bin/activate.fish" *from fish*
<<<<<<< HEAD
# (https://fishshell.com/); you cannot run it directly.
=======
# (https://fishshell.com/). You cannot run it directly.
>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa

function deactivate  -d "Exit virtual environment and return to normal shell environment"
    # reset old environment variables
    if test -n "$_OLD_VIRTUAL_PATH"
        set -gx PATH $_OLD_VIRTUAL_PATH
        set -e _OLD_VIRTUAL_PATH
    end
    if test -n "$_OLD_VIRTUAL_PYTHONHOME"
        set -gx PYTHONHOME $_OLD_VIRTUAL_PYTHONHOME
        set -e _OLD_VIRTUAL_PYTHONHOME
    end

    if test -n "$_OLD_FISH_PROMPT_OVERRIDE"
        set -e _OLD_FISH_PROMPT_OVERRIDE
        # prevents error when using nested fish instances (Issue #93858)
        if functions -q _old_fish_prompt
            functions -e fish_prompt
            functions -c _old_fish_prompt fish_prompt
            functions -e _old_fish_prompt
        end
    end

    set -e VIRTUAL_ENV
    set -e VIRTUAL_ENV_PROMPT
    if test "$argv[1]" != "nondestructive"
        # Self-destruct!
        functions -e deactivate
    end
end

# Unset irrelevant variables.
deactivate nondestructive

<<<<<<< HEAD
set -gx VIRTUAL_ENV "/Users/na61/Desktop/US stockmarket Algotrading /algo-trade-platform/venv"

set -gx _OLD_VIRTUAL_PATH $PATH
set -gx PATH "$VIRTUAL_ENV/bin" $PATH
=======
set -gx VIRTUAL_ENV /home/anurag/Desktop/Algo-Trading/algo-trade-platform/venv

set -gx _OLD_VIRTUAL_PATH $PATH
set -gx PATH "$VIRTUAL_ENV/"bin $PATH
>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa

# Unset PYTHONHOME if set.
if set -q PYTHONHOME
    set -gx _OLD_VIRTUAL_PYTHONHOME $PYTHONHOME
    set -e PYTHONHOME
end

if test -z "$VIRTUAL_ENV_DISABLE_PROMPT"
    # fish uses a function instead of an env var to generate the prompt.

    # Save the current fish_prompt function as the function _old_fish_prompt.
    functions -c fish_prompt _old_fish_prompt

    # With the original prompt function renamed, we can override with our own.
    function fish_prompt
        # Save the return status of the last command.
        set -l old_status $status

        # Output the venv prompt; color taken from the blue of the Python logo.
<<<<<<< HEAD
        printf "%s%s%s" (set_color 4B8BBE) "(venv) " (set_color normal)
=======
        printf "%s%s%s" (set_color 4B8BBE) '(venv) ' (set_color normal)
>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa

        # Restore the return status of the previous command.
        echo "exit $old_status" | .
        # Output the original/"old" prompt.
        _old_fish_prompt
    end

    set -gx _OLD_FISH_PROMPT_OVERRIDE "$VIRTUAL_ENV"
<<<<<<< HEAD
    set -gx VIRTUAL_ENV_PROMPT "(venv) "
=======
    set -gx VIRTUAL_ENV_PROMPT '(venv) '
>>>>>>> 001267c5e5004fb8de3c6b8bbc2d0dda30761cfa
end
