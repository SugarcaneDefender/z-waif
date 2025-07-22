{
  description = "Development flake for z-waif.";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
  };
  outputs = { self, nixpkgs, flake-utils, pyproject-nix, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: rec {
              pythonPackagesOverlays = (prev.pythonPackagesOverlays or [ ]) ++ [
                (python-final: python-prev: with python3.pkgs; pythonPackages // {
                  # Package renames
                  discord-py = discordpy;
                  silero-vad = pysilero-vad;
                })
              ];
              python3 = let
                self = prev.python311.override {
                  inherit self;
                  packageOverrides = prev.lib.composeManyExtensions final.pythonPackagesOverlays;
                };
              in self;
              python = python3;
              python311 = python3;
              python311Packages = python3.pkgs;
            })
          ];
        };
        libs = with pkgs; [ portaudio libglvnd glib ];
        project = pyproject-nix.lib.project.loadRequirementsTxt {
          requirements = builtins.readFile ./requirements.txt;
          projectRoot = ./.;
        };
        pythonEnv = with pkgs; 
          # assert project.validators.validateVersionConstraints { python = python3; } == { };
          (
            python3.withPackages (project.renderers.withPackages { inherit python; }) # pythonPackages = python3.pkgs; })
          );
        pythonPackages = with pkgs; {
          # mouse package for requirements.txt
          mouse = let
            version = "0.7.1";
            pname = "mouse";
          in python3.pkgs.buildPythonPackage {
            inherit pname version;
            src = fetchFromGitHub {
              owner = "boppreh";
              repo = "mouse";
              tag = "v${version}";
              hash = lib.fakeHash;
            };
            propagatedBuildInputs = [ python3.pkgs.pynput ];
          };
          # Waiting on upstream to mark as linux supported
          pyvts = let
            version = "0.3.3";
            pname = "pyvts";
          in python3.pkgs.buildPythonPackage {
            inherit pname version;
            src = fetchPypi {
              inherit pname version;
              sha256 = "sha256-3s8ymaORzi44/8w/ssr3Hwaye5yit1gdxal+YmINosQ=";
            };
            propagatedBuildInputs = [ ];
          };
          twitchio = let
            version = "2.9.1";
            pname = "twitchio";
          in python3.pkgs.buildPythonPackage {
            inherit pname version;
            src = fetchFromGitHub {
              owner = "PythonistaGuild";
              repo = "twitchio";
              tag = "v${version}";
              hash = "sha256-JbRpIMwrmcpV4juEoI3epE+8n97XkKolFFpYsXmH7LE=";
            };
            propagatedBuildInputs = [ ];
          };
      };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs;
            [ mypy python3 python311Packages.pip git ] ++ libs;
          packages = [ pythonEnv ];
          shellHook = ''
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.portaudio.out}
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.libglvnd.out}/lib
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.glib.out}/lib
          '';
          # Load the venv in the .envrc file
        };
        # This really should be a seperate file lmao
        packages = with pkgs; rec {
          inherit python3;
          python = python3;
          python311 = python3;
        } // pythonPackages;
      });
}
