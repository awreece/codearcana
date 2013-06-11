Title: My <tt>zsh</tt> theme
Date: 2013-11-06
Tags: zsh

I spent some time this week switching from `bash` to `zsh`
and making a theme for
[`oh-my-zsh`](https://github.com/robbyrussell/oh-my-zsh) 
for myself. I'm not quite done, but I am pretty pleased with
the results. First, a screenshot:

![`zsh` theme](|filename|/../images/zsh_theme.png "My `zsh` theme")

And a step by step explanation:

-     By default, the prompt is very minimalist (the current directory and a % or a # depending on the privileges of the shell).
-     In the right hand prompt, the execution time of the last command is displayed. It is colored green if the command returned successfully and red otherwise.
-     The number of background processes is displayed (but only if there are background processes).
-     If the path to the current directory is long, it is also displayed in the right hand side.
-     The user and hostname are displayed (only) if logged in over `ssh`.
-     Since this is `zsh`, the right hand prompt disappears if the line is long enough.

The best part? On Mac OSX, I get notifications if a program completes and the terminal doesn't have focus:

![`zsh` theme popup](|filename|/../images/zsh_theme_popup.png "A sample notification - click to focus on the terminal window.")

Source is in [my fork of `oh-my-zsh`](https://github.com/awreece/oh-my-zsh/blob/master/themes/awreece.zsh-theme).