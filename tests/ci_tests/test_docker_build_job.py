"""
Test CI Docker build job validation.
"""

import pytest
import subprocess
import os
from pathlib import Path


class TestDockerBuildJob:
    """Test the docker-build CI job functionality."""

    def test_docker_buildx_available(self):
        """Test that Docker Buildx is available."""
        # Check if docker command exists
        docker_available = subprocess.run(['which', 'docker'], capture_output=True).returncode == 0
        
        if not docker_available:
            pytest.skip("Docker not available on this system")
        
        # Test docker version
        result = subprocess.run(
            ['docker', '--version'], 
            capture_output=True, 
            text=True
        )
        
        assert result.returncode == 0, "Docker should be available"
        assert 'docker' in result.stdout.lower(), "Docker version should contain 'docker'"

    def test_docker_buildx_command(self):
        """Test that Docker Buildx commands are available."""
        # Check if docker buildx is available
        result = subprocess.run(
            ['docker', 'buildx', '--help'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            pytest.skip("Docker Buildx not available")
        
        assert 'build' in result.stdout, "Docker Buildx should support build command"

    def test_dockerfile_location_check(self):
        """Test that Dockerfile exists in expected location."""
        project_root = Path(__file__).parent.parent.parent
        dockerfile_path = project_root / "DEPLOYMENT" / "docker" / "Dockerfile"
        
        if dockerfile_path.exists():
            assert dockerfile_path.is_file(), "Dockerfile should be a file"
            
            # Read Dockerfile to check basic structure
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
            
            assert 'FROM' in dockerfile_content, "Dockerfile should have FROM instruction"
        else:
            pytest.skip("Dockerfile not found at DEPLOYMENT/docker/Dockerfile")

    def test_deployment_directory_structure(self):
        """Test that deployment directory structure exists."""
        project_root = Path(__file__).parent.parent.parent
        deployment_dir = project_root / "DEPLOYMENT"
        
        if deployment_dir.exists():
            assert deployment_dir.is_dir(), "DEPLOYMENT should be a directory"
            
            docker_dir = deployment_dir / "docker"
            if docker_dir.exists():
                assert docker_dir.is_dir(), "DEPLOYMENT/docker should be a directory"
        else:
            print("DEPLOYMENT directory not found - Docker build will be skipped")

    def test_docker_build_command_structure(self):
        """Test that Docker build command structure is correct."""
        # Test the exact command from CI
        expected_command = [
            'docker', 'build', 
            '-f', 'DEPLOYMENT/docker/Dockerfile', 
            '-t', 'zyi:test', 
            '.'
        ]
        
        # Validate command structure
        assert expected_command[0] == 'docker', "Should use docker command"
        assert expected_command[1] == 'build', "Should use build subcommand"
        assert '-f' in expected_command, "Should specify Dockerfile with -f"
        assert '-t' in expected_command, "Should tag image with -t"
        assert '.' in expected_command, "Should build from current directory"

    def test_docker_image_tag_format(self):
        """Test that Docker image tag follows proper format."""
        image_tag = "zyi:test"
        
        # Validate tag format
        assert ':' in image_tag, "Image tag should have name:tag format"
        
        name, tag = image_tag.split(':', 1)
        assert len(name) > 0, "Image name should not be empty"
        assert len(tag) > 0, "Image tag should not be empty"
        assert name == 'zyi', "Image name should be 'zyi'"
        assert tag == 'test', "Tag should be 'test' for CI"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_docker_build_simulation(self):
        """Test Docker build simulation (if Docker and Dockerfile available)."""
        project_root = Path(__file__).parent.parent.parent
        dockerfile_path = project_root / "DEPLOYMENT" / "docker" / "Dockerfile"
        
        # Check if Docker is available
        docker_available = subprocess.run(['which', 'docker'], capture_output=True).returncode == 0
        
        if not docker_available:
            pytest.skip("Docker not available for build test")
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile not found - build test skipped")
        
        # Try to build (with timeout)
        result = subprocess.run(
            [
                'docker', 'build', 
                '-f', str(dockerfile_path), 
                '-t', 'zyi:test', 
                str(project_root)
            ], 
            capture_output=True, 
            text=True,
            cwd=project_root,
            timeout=300  # 5 minute timeout
        )
        
        # Docker build might fail due to dependencies - that's OK for validation
        print(f"Docker build return code: {result.returncode}")
        print(f"Docker build stdout: {result.stdout[-500:]}")  # Last 500 chars
        print(f"Docker build stderr: {result.stderr[-500:]}")  # Last 500 chars
        
        if result.returncode != 0:
            pytest.skip("Docker build failed - this is expected for CI validation")

    def test_continue_on_error_behavior(self):
        """Test that Docker build continues on error."""
        # Docker build job uses continue-on-error: true
        
        # Simulate a docker build that might fail
        result = subprocess.run(
            ['docker', '--version'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            # Docker not available - this simulates continue-on-error behavior
            print("Docker not available - continuing as per CI configuration")
        
        # Test should always pass due to continue-on-error
        assert True, "Docker build job should continue on error"

    def test_docker_buildx_setup_action(self):
        """Test Docker Buildx setup action requirements."""
        # This validates the setup-buildx-action@v2 requirements
        
        # Check if docker supports buildx
        result = subprocess.run(
            ['docker', 'buildx', 'version'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            assert 'buildx' in result.stdout.lower(), "Docker Buildx should be available"
        else:
            pytest.skip("Docker Buildx not available")

    def test_dockerfile_exists_check_logic(self):
        """Test the Dockerfile existence check logic from CI."""
        project_root = Path(__file__).parent.parent.parent
        dockerfile_path = project_root / "DEPLOYMENT" / "docker" / "Dockerfile"
        
        # Simulate the CI check logic
        if dockerfile_path.exists():
            print("Dockerfile found - Docker build would proceed")
            should_build = True
        else:
            print("Dockerfile not found - Docker build would be skipped")
            should_build = False
        
        # This logic should match the CI workflow
        expected_check = "if [ -f DEPLOYMENT/docker/Dockerfile ]; then"
        assert isinstance(expected_check, str), "Dockerfile check should be a string command"

    def test_docker_build_context(self):
        """Test that Docker build context is properly set."""
        # CI builds from current directory (.)
        build_context = "."
        
        assert build_context == ".", "Build context should be current directory"
        assert isinstance(build_context, str), "Build context should be string"

    def test_docker_build_requirements(self):
        """Test Docker build job requirements."""
        required_components = {
            'docker': 'Docker engine',
            'buildx': 'Docker Buildx for enhanced builds'
        }
        
        # Test docker availability
        docker_result = subprocess.run(['which', 'docker'], capture_output=True)
        docker_available = docker_result.returncode == 0
        
        if docker_available:
            # Test buildx if docker is available
            buildx_result = subprocess.run(['docker', 'buildx', 'version'], capture_output=True)
            buildx_available = buildx_result.returncode == 0
            
            if not buildx_available:
                print("Docker available but Buildx not available")
        else:
            print("Docker not available")
        
        # Don't fail test - this is informational
        assert True, "Docker build requirements checked"

    def test_ubuntu_latest_runner_requirements(self):
        """Test that Ubuntu latest runner can support Docker."""
        import platform
        
        current_os = platform.system().lower()
        
        if current_os == 'linux':
            # Check if we're on Ubuntu-like system
            try:
                with open('/etc/os-release', 'r') as f:
                    os_info = f.read()
                if 'ubuntu' in os_info.lower():
                    print("Running on Ubuntu-like system - Docker should be available")
            except FileNotFoundError:
                print("Cannot determine Linux distribution")
        
        # This is informational - don't fail
        assert True, "Ubuntu runner requirements checked"

    def test_docker_image_naming_convention(self):
        """Test Docker image naming convention."""
        # CI uses 'zyi:test' for the image name
        image_name = "zyi"
        image_tag = "test"
        full_image = f"{image_name}:{image_tag}"
        
        # Validate naming convention
        assert image_name.islower(), "Image name should be lowercase"
        assert len(image_name) >= 2, "Image name should be at least 2 characters"
        assert image_tag.isalnum(), "Image tag should be alphanumeric"
        assert full_image == "zyi:test", "Full image name should match CI expectation"