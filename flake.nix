{
  description = "diffoscope-server";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  #inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        diffoscope-server = pkgs.python3Packages.buildPythonPackage {
          pname = "diffoscope-server";
          version = "0.0.1";
          src = ./.;
          propagatedBuildInputs = with pkgs.python3Packages; [
            flask
          ] ++ (with pkgs; [
            diffoscope
          ]
          );
          doCheck = false;
        };
        waitressEnv = pkgs.python3.withPackages (p: with p; [
          waitress diffoscope-server
        ]);
        app = flake-utils.lib.mkApp { drv = diffoscope-server; };
      in
      {
        packages.diffoscope-server = diffoscope-server;
        packages.waitressEnv = waitressEnv;
        defaultPackage = diffoscope-server;
        apps.diffoscope-server = app;
        defaultApp = app;
        devShell = import ./shell.nix { inherit pkgs; };
      }
    )) // (
    let
      nixosModule = { config, lib, pkgs, ... }:
        let
          cfg = config.services.diffoscope-server;
          system = pkgs.system;
        in {
          options.services.diffoscope-server = {
            enable = lib.mkOption {
              description = "Enable diffoscope-server service";
              type = lib.types.bool;
              default = false;
            };
            address = lib.mkOption {
              description = "Address to listen to";
              type = lib.types.str;
              default = "127.0.0.1";
            };
            port = lib.mkOption {
              description = "Port to listen to";
              type = lib.types.int;
              default = 8080;
            };
          };
          config = lib.mkIf cfg.enable {
            users = {
              users.diffoscope-server.home = "/var/lib/diffoscope-server";
              users.diffoscope-server.createHome = true;
              users.diffoscope-server.isSystemUser = true;
              users.diffoscope-server.group = "diffoscope-server";
              groups.diffoscope-server = {};
            };
            systemd.services.diffoscope-server = {
              path = [ pkgs.diffoscopeMinimal ];
              description = "diffoscope-server";
              wantedBy = [ "multi-user.target" ];
              after = [ "network.target" ];
              serviceConfig = {
                ExecStart = lib.escapeShellArgs [
                  "${self.packages.${system}.waitressEnv}/bin/waitress-serve"
                  "--threads" "8"
                  "--listen" "${cfg.address}:${builtins.toString cfg.port}"
                  "--call" "diffoscope_server.main:create_app"
                ];
                Restart = "on-failure";
                User = "diffoscope-server";
                Group = "diffoscope-server";
              };
            };
          };
        };
      in
      {
        inherit nixosModule;
        nixosModules = { diffoscope-server = nixosModule; default = nixosModule; };
      }
    );
}
