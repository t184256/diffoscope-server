{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    diffoscopeMinimal
    (python3.withPackages (ps: with ps; [
      flask
    ]))
  ];
  nativeBuildInputs = (with pkgs.python3Packages; [
    coverage
    flake8
    flake8-import-order
  ]) ++ (with pkgs; [
    codespell
  ]);
}
