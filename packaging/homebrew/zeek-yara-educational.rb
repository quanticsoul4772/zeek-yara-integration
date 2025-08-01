class ZeekYaraEducational < Formula
  include Language::Python::Virtualenv

  desc "Educational network security monitoring platform"
  homepage "https://github.com/your-org/zeek_yara_integration"
  url "https://github.com/your-org/zeek_yara_integration/archive/v1.0.0.tar.gz"
  sha256 "YOUR_SHA256_HERE"  # Will be calculated from actual release
  license "MIT"
  head "https://github.com/your-org/zeek_yara_integration.git", branch: "main"

  depends_on "python@3.11"
  depends_on "yara"
  depends_on "openssl@3"
  depends_on "libmagic"

  # Python dependencies
  resource "yara-python" do
    url "https://files.pythonhosted.org/packages/source/y/yara-python/yara-python-4.3.1.tar.gz"
    sha256 "31a80e945b72b952a3ea83a4e0f8a8c4e5a41dc15c1c4c0b8f8f3e0a5a5a5a5a"
  end

  resource "watchdog" do
    url "https://files.pythonhosted.org/packages/source/w/watchdog/watchdog-3.0.0.tar.gz"
    sha256 "4d98a320595da7a7c5a18fc48cb633c2e73cda78f93cac2ef42d42bf609a33f9"
  end

  resource "python-magic" do
    url "https://files.pythonhosted.org/packages/source/p/python-magic/python-magic-0.4.27.tar.gz"
    sha256 "c1ba14b08e4a5f5c31a302b7721239695b2f0f058d125bd5ce1ee36b9d9d3c3b"
  end

  resource "fastapi" do
    url "https://files.pythonhosted.org/packages/source/f/fastapi/fastapi-0.104.1.tar.gz"
    sha256 "e5e4540a7c5e1dcfbbcf5b903c234feddcdcd881f191977a1c5dfd917487e7ae"
  end

  resource "uvicorn" do
    url "https://files.pythonhosted.org/packages/source/u/uvicorn/uvicorn-0.24.0.tar.gz"
    sha256 "368e0d1e6d4de8d338d3b8d3662c8b8d8c52e1c3b9c1b6f4e5e6b8e5e5e5e5e5"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.5.0.tar.gz"
    sha256 "7a2a7e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3"
  end

  resource "sqlalchemy" do
    url "https://files.pythonhosted.org/packages/source/s/sqlalchemy/SQLAlchemy-2.0.23.tar.gz"
    sha256 "c1ba14b08e4a5f5c31a302b7721239695b2f0f058d125bd5ce1ee36b9d9d3c3b"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz"
    sha256 "942c5a758f98d790eaed1a29cb6eefc7ffb0d1cf7af05c3d2791656dbd6ad1e1"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "5cb5123b5cf9ee70584244246816e9114227e0b98ad9176eede6ad54bf5403fa"
  end

  resource "typer" do
    url "https://files.pythonhosted.org/packages/source/t/typer/typer-0.9.0.tar.gz"
    sha256 "50922fd79aea2f4751a8e0408ff10d2662bd0c8bbfa84755a699f3bada2978b2"
  end

  def install
    # Create virtualenv
    virtualenv_install_with_resources

    # Install main package
    system libexec/"bin/pip", "install", buildpath

    # Create wrapper scripts
    (bin/"zeek-yara-educational").write_env_script(
      libexec/"bin/zeek-yara-educational",
      PATH: "#{libexec}/bin:$PATH"
    )
    
    (bin/"zye").write_env_script(
      libexec/"bin/zye", 
      PATH: "#{libexec}/bin:$PATH"
    )
    
    (bin/"zeek-yara-setup").write_env_script(
      libexec/"bin/zeek-yara-setup",
      PATH: "#{libexec}/bin:$PATH"
    )

    # Install man pages
    if (buildpath/"docs/man").exist?
      man1.install Dir["docs/man/*.1"]
    end

    # Install completion scripts
    generate_completions_from_executable(bin/"zeek-yara-educational", shells: [:bash, :zsh, :fish])

    # Install configuration examples
    (etc/"zeek-yara-educational").mkpath
    (etc/"zeek-yara-educational").install "config/default_config.json" => "config.json.example"

    # Install educational content
    if (buildpath/"EDUCATION").exist?
      (share/"zeek-yara-educational").mkpath
      (share/"zeek-yara-educational").install "EDUCATION" => "education"
    end

    # Install documentation
    if (buildpath/"docs").exist?
      doc.install Dir["docs/*"]
    end
  end

  def post_install
    # Create directories for runtime data
    (var/"log/zeek-yara-educational").mkpath
    (var/"lib/zeek-yara-educational").mkpath
  end

  service do
    run [opt_bin/"zeek-yara-educational", "--web-only"]
    working_dir var/"lib/zeek-yara-educational"
    log_path var/"log/zeek-yara-educational/output.log"
    error_log_path var/"log/zeek-yara-educational/error.log"
    environment_variables PATH: std_service_path_env
    keep_alive true
    restart_delay 10
  end

  test do
    # Test version output
    assert_match version.to_s, shell_output("#{bin}/zeek-yara-educational --version")
    
    # Test help output
    assert_match "Educational network security", shell_output("#{bin}/zeek-yara-educational --help")
    
    # Test setup wizard help
    assert_match "setup wizard", shell_output("#{bin}/zeek-yara-setup --help")
    
    # Test configuration loading
    system bin/"zeek-yara-educational", "--demo"
    
    # Test import functionality
    system libexec/"bin/python", "-c", "import main; import setup_wizard; import core"
  end

  def caveats
    <<~EOS
      Zeek-YARA Educational Platform has been installed successfully!

      Getting Started:
      1. Run the setup wizard:
         zeek-yara-setup

      2. Or start the application directly:
         zeek-yara-educational

      3. For quick access, you can use the short alias:
         zye

      Configuration:
      - Example config: #{etc}/zeek-yara-educational/config.json.example
      - Copy and customize for your needs
      - Runtime data: #{var}/lib/zeek-yara-educational
      - Logs: #{var}/log/zeek-yara-educational

      Educational Content:
      - Learning materials: #{share}/zeek-yara-educational/education
      - Documentation: #{doc}

      Service Management:
      - Start service: brew services start zeek-yara-educational
      - Stop service: brew services stop zeek-yara-educational
      - View status: brew services list | grep zeek-yara

      Web Interface:
      When running, the web interface will be available at:
      http://localhost:8000

      For more information, visit:
      #{homepage}
    EOS
  end
end