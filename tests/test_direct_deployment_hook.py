"""Exercise direct deployment through real Git pushes to a temporary server repository."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = (
    ROOT
    / "{{cookiecutter.repostory_name}}"
    / "bin"
    / "{% if cookiecutter.deployment_type == 'direct' %}deploy-update-hook.sh{% endif %}"
)


class DirectDeploymentHookTests(unittest.TestCase):
    def test_failed_deployment_rejects_push_and_allows_retry(self):
        for branch in ("main", "master"):
            with self.subTest(local_branch=branch), tempfile.TemporaryDirectory() as directory:
                self.check_workflow(Path(directory), branch)

    def check_workflow(self, base, branch):
        local = base / "local"
        server = base / "server.git"
        worktree = base / "application"
        local.mkdir()
        worktree.mkdir()

        def git(*args, cwd=local, check=True):
            return subprocess.run(
                ["git", *args],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=check,
                env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
            )

        def commit(version):
            (local / "version.txt").write_text(version)
            git("add", ".")
            git("commit", "-m", version)
            return git("rev-parse", "HEAD").stdout.strip()

        git("init", "--bare", "--initial-branch=master", str(server))
        git("init", f"--initial-branch={branch}")
        git("config", "user.name", "Deployment test")
        git("config", "user.email", "deployment@example.invalid")
        deploy = local / "deploy.sh"
        deploy.write_text(
            '#!/bin/sh\nset -eu\n[ ! -f "$GIT_DIR/blocked" ]\ngit rev-parse HEAD >> "$GIT_DIR/deployments"\n'
        )
        deploy.chmod(0o755)
        initial = commit("initial")
        git("remote", "add", "production", str(server))
        git("push", "production", "HEAD:master")
        self.assertEqual(list(worktree.iterdir()), [])

        # Install the actual template hook with only its server paths rendered for this fixture.
        hook = server / "hooks/update"
        hook.write_text(
            HOOK.read_text()
            .replace("/root/repos/{{ cookiecutter.repostory_name }}.git", str(server))
            .replace("/root/domains/{{ cookiecutter.repostory_name }}", str(worktree))
        )
        hook.chmod(0o755)

        updated = commit("updated")
        git("push", "production", "HEAD:master")
        self.assertEqual(git("rev-parse", "refs/heads/master", cwd=server).stdout.strip(), updated)
        self.assertEqual((worktree / "version.txt").read_text(), "updated")
        deployments = server / "deployments"
        self.assertEqual(deployments.read_text().splitlines(), [updated])

        # Other refs, including a tag named master, must not deploy.
        git("push", "production", "HEAD:feature", "HEAD:refs/tags/master")
        self.assertEqual(deployments.read_text().splitlines(), [updated])
        git("push", "production", ":refs/tags/master")
        git("push", "production", "HEAD:master")
        self.assertEqual(deployments.read_text().splitlines(), [updated])
        deleted = git("push", "production", ":master", check=False)
        self.assertNotEqual(deleted.returncode, 0)
        self.assertEqual(git("rev-parse", "refs/heads/master", cwd=server).stdout.strip(), updated)
        self.assertEqual(deployments.read_text().splitlines(), [updated])

        incoming = commit("blocked version")
        blocker = server / "blocked"
        blocker.touch()
        failed = git("push", "production", "HEAD:master", check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("hook declined", failed.stderr)
        self.assertEqual(git("rev-parse", "refs/heads/master", cwd=server).stdout.strip(), updated)
        self.assertEqual(git("rev-parse", "HEAD", cwd=server).stdout.strip(), incoming)
        self.assertEqual((worktree / "version.txt").read_text(), "blocked version")
        self.assertEqual(deployments.read_text().splitlines(), [updated])

        blocker.unlink()
        git("push", "production", "HEAD:master")
        self.assertEqual(git("rev-parse", "refs/heads/master", cwd=server).stdout.strip(), incoming)
        self.assertEqual(deployments.read_text().splitlines(), [updated, incoming])

        git("fetch", "production")
        git("branch", "older-version", initial)
        git("push", "--force-with-lease", "production", "older-version:master")
        self.assertEqual(git("rev-parse", "refs/heads/master", cwd=server).stdout.strip(), initial)
        self.assertEqual(deployments.read_text().splitlines(), [updated, incoming, initial])


if __name__ == "__main__":
    unittest.main()
