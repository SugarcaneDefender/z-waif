{
  description = "Development flake for z-waif.";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        libs = with pkgs; [ portaudio libglvnd glib ];
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs;
            [ mypy python311Full python311Packages.pip git ] ++ libs;
          shellHook = ''
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.portaudio.out}
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.libglvnd.out}/lib
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.glib.out}/lib
          '';
          # Load the venv in the .envrc file
        };
      });
}
