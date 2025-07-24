{
  description = "Development flake for z-waif.";
  nixConfig = {
    extra-substituters = "https://z-waif.cachix.org";
    extra-trusted-public-keys = "z-waif.cachix.org-1:w4aiXXlhHNzyrV/tkrQvJHnBLLw8eWoYiPwJiNMcmI0=";
    download-buffer-size = 2147483648; # 2 GiB
  };
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # e2fspkgs.url = "github:NixOS/nixpkgs/nixos-unstable?rev=d8c8ccaeca94ed9da559170ee77d6d13a6649212";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
  };
  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      pyproject-nix,
      ...
    }@inputs:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        pypkgs = import nixpkgs {
          inherit system;
          overlays = [
            # e2fsprogs
            (final: prev: {
              # e2fsprogs = (import inputs.e2fspkgs {inherit system;}).e2fsprogs;
              e2fsprogs = (
                (prev.e2fsprogs.override { withFuse = true; }).overrideAttrs (
                  final: prev: {
                    postInstall = (prev.postInstall or "") + ''
                      cp $fuse2fs/bin/fuse2fs $bin/bin
                    '';
                    doCheck = false; # tests fail on btrfs
                  }
                )
              );
            })
            # Python
            (final: prev: rec {
              pythonPackagesOverlays = (prev.pythonPackagesOverlays or [ ]) ++ [
                (
                  python-final: python-prev:
                  with python3.pkgs;
                  pythonPackages
                  // {
                    # Package renames
                    discord-py = discordpy;
                    silero-vad = pysilero-vad;
                  }
                )
              ];
              newPython311 =
                let
                  self = prev.python311.override {
                    inherit self;
                    packageOverrides = prev.lib.composeManyExtensions final.pythonPackagesOverlays;
                  };
                in
                self;
              newPython311Packages = newPython311.pkgs;
            })
          ];
        };
        python3 = pypkgs.newPython311;
        libs = with pkgs; [
          portaudio
          libglvnd
          glib
        ];
        project = pyproject-nix.lib.project.loadRequirementsTxt {
          requirements = builtins.readFile ./requirements.txt;
          projectRoot = ./.;
        };
        pythonEnv =
          # assert project.validators.validateVersionConstraints { python = python3; } == { };
          (
            python3.withPackages (
              project.renderers.withPackages {
                python = python3;
                pythonPackages = python3.pkgs;
              }
            )
          );
        pythonPackages = with pkgs; {
          # mouse package for requirements.txt
          mouse =
            let
              version = "0.7.1";
              pname = "mouse";
            in
            python3.pkgs.buildPythonPackage {
              inherit pname version;
              src = fetchFromGitHub {
                owner = "boppreh";
                repo = "mouse";
                tag = "v${version}";
                hash = "sha256-vVUEmW7maSMONoVHym/6NPaxgOL87Br6/ue7nbd5XR8=";
              };
              propagatedBuildInputs = [ python3.pkgs.pynput ];
            };
          # Waiting on upstream to mark as linux supported
          pyvts =
            let
              version = "0.3.3";
              pname = "pyvts";
            in
            python3.pkgs.buildPythonPackage {
              inherit pname version;
              src = fetchPypi {
                inherit pname version;
                sha256 = "sha256-3s8ymaORzi44/8w/ssr3Hwaye5yit1gdxal+YmINosQ=";
              };
              propagatedBuildInputs = [ ];
            };
          twitchio =
            let
              version = "2.9.1";
              pname = "twitchio";
            in
            python3.pkgs.buildPythonPackage {
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
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs =
            with pkgs;
            [
              mypy
              python3
              python311Packages.pip
              git
            ]
            ++ libs;
          packages = [ pythonEnv ];
          shellHook = ''
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.portaudio.out}
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.libglvnd.out}/lib
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.glib.out}/lib
          '';
          # Load the venv in the .envrc file
        };
        # This really should be a seperate file lmao
        packages =
          with pkgs;
          rec {
            inherit
              python3
              # python311Packages
              e2fsprogs
              pythonEnv
              ;
            python = python3;
            python311 = python3;
          }
          // pythonPackages;
      }
    );
}
