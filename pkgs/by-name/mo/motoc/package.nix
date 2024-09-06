{
  lib,
  rustPlatform,
  fetchFromGitHub,
  openxr-loader,
  nix-update-script,
}:

rustPlatform.buildRustPackage rec {
  pname = "motoc";
  version = "0.2.0";

  src = fetchFromGitHub {
    owner = "galister";
    repo = "motoc";
    rev = "refs/tags/v${version}";
    hash = "sha256-7p25F2bRba3LxS8UAkHvhb+GyOsKUMj7bhiK5ZJ0Jkk=";
  };

  cargoLock = {
    lockFile = ./Cargo.lock;
    outputHashes = {
      "libmonado-rs-0.1.0" = "sha256-bbbo/Mkix6nUGLwplvj6m8IXOcZY5UoWc1xZnI67IlU=";
      "openxr-0.19.0" = "sha256-kbEYoN4UvUEaZA9LJWEKx1X1r+l91GjTWs1hNXhr7cw=";
    };
  };

  buildInputs = [
    openxr-loader
  ];

  passthru.updateScript = nix-update-script { };

  meta = {
    description = "MOnado Tracking Origin Calibration program";
    homepage = "https://github.com/galister/motoc";
    changelog = "https://github.com/galister/motoc/releases";
    license = lib.licenses.gpl3Plus;
    maintainers = with lib.maintainers; [ pandapip1 ];
    mainProgram = "motoc";
    platforms = lib.platforms.all;
  };
}
