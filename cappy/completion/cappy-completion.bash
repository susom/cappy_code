#!/usr/bin/env bash
# Bash completion for cappy command

_cappy_completions()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    local commands="scan search read run apply agent chat config analytics --version --help"
    
    # If we're completing the first argument
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    # Get the main command
    local cmd="${COMP_WORDS[1]}"
    
    case "${cmd}" in
        scan)
            # Complete with directories
            COMPREPLY=( $(compgen -d -- ${cur}) )
            ;;
        search)
            if [ $COMP_CWORD -eq 2 ]; then
                # Pattern argument - no completion
                return 0
            else
                # Path argument - complete with directories
                COMPREPLY=( $(compgen -d -- ${cur}) )
            fi
            ;;
        read|apply)
            # Complete with files
            COMPREPLY=( $(compgen -f -- ${cur}) )
            ;;
        run)
            # No completion for commands
            return 0
            ;;
        agent)
            if [ $COMP_CWORD -eq 2 ]; then
                # Task description - no completion
                return 0
            else
                case "${prev}" in
                    --model)
                        local models="gpt-4.1 o1 gemini25pro"
                        COMPREPLY=( $(compgen -W "${models}" -- ${cur}) )
                        ;;
                    --max-iterations)
                        # Number - no completion
                        return 0
                        ;;
                    *)
                        local opts="--model --max-iterations --quiet"
                        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
                        ;;
                esac
            fi
            ;;
        chat)
            case "${prev}" in
                --model)
                    local models="gpt-4.1 o1 gemini25pro"
                    COMPREPLY=( $(compgen -W "${models}" -- ${cur}) )
                    ;;
                *)
                    local opts="--model"
                    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
                    ;;
            esac
            ;;
        config)
            if [ $COMP_CWORD -eq 2 ]; then
                local subcommands="validate"
                COMPREPLY=( $(compgen -W "${subcommands}" -- ${cur}) )
            else
                case "${prev}" in
                    --config)
                        # Complete with .yaml files
                        COMPREPLY=( $(compgen -f -X '!*.yaml' -- ${cur}) )
                        ;;
                    *)
                        local opts="--config"
                        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
                        ;;
                esac
            fi
            ;;
        analytics)
            case "${prev}" in
                --days)
                    # Number - no completion
                    return 0
                    ;;
                *)
                    local opts="--days"
                    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
                    ;;
            esac
            ;;
    esac
    
    return 0
}

complete -F _cappy_completions cappy
