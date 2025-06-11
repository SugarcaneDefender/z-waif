{
  description = "Fully local & open source AI Waifu.";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ python311Full ];
          shellHook = "./startup.sh";
        };
        packages.default = let startup = builtins.readFile ./startup.sh;
        in pkgs.mkDerivation {
          pname = "z-waif";
          src = ./.;
          nativeBuildInputs = with pkgs; [ python311 ];
          my-script = (pkgs.writeScriptBin my-name my-src).overrideAttrs (old: {
            buildCommand = ''
              ${old.buildCommand}
               patchShebangs $out'';
          });

        };
      });
}
