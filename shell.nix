{ pkgs ? import <nixpkgs> {} }:

with pkgs;

let myPython = python39.buildEnv.override {
      extraLibs = with python39Packages; [
        # Common Libs
        rich
        numpy
        matplotlib
        # scipy
        # torch
        
        # Doom Emacs Libs
        black
        pyflakes
        isort
        nose
        pytest

        # For Discord-Bot
        python-dotenv # Env
        discordpy # Discord
        pynacl # Voice
      ];
    };
in

mkShell {
  buildInputs = [
    myPython
    nodePackages.pyright # LSP
    pipenv # Doom

    ffmpeg # Voice
  ];
}
