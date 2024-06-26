{ pkgs, config, lib, ... }:

with lib;

let
  cfg = config.programs.zmap;
in {
  options.programs.zmap = {
    enable = mkEnableOption "ZMap, a network scanner designed for Internet-wide network surveys";
  };

  config = mkIf cfg.enable {
    environment.systemPackages = [ pkgs.zmap ];

    environment.etc."zmap/blacklist.conf".source = "${pkgs.zmap}/etc/zmap/blacklist.conf";
    environment.etc."zmap/zmap.conf".source = "${pkgs.zmap}/etc/zmap.conf";
  };
}
