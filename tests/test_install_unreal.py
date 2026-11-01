import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import install_unreal as installer


class RepositoryValidationTests(unittest.TestCase):
    def test_normalizes_explicit_github_fork(self):
        self.assertEqual(
            installer.validate_repository('https://github.com/MikeDudikov/UnrealEngine'),
            'https://github.com/MikeDudikov/UnrealEngine.git',
        )
        self.assertEqual(installer.validate_repository(installer.REMOTE), installer.REMOTE)

    def test_rejects_other_hosts_credentials_and_url_extras(self):
        for repository in [
            'http://github.com/owner/repo', 'ssh://git@github.com/owner/repo',
            'https://user:password@github.com/owner/repo',
            'https://github.com.example.invalid/owner/repo',
            'https://github.com:443/owner/repo',
            'https://github.com/owner/repo?token=example',
            'https://github.com/owner/repo#fragment',
            'https://github.com/owner/repo/extra',
            'https://github.com/owner/..', 'https://github.com/owner/.git',
            '/tmp/local-repo', 'https://github.com/owner/repo\n',
        ]:
            with self.subTest(repository=repository), self.assertRaises(ValueError):
                installer.validate_repository(repository)


class ReleaseSelectionTests(unittest.TestCase):
    def test_orders_versions_numerically(self):
        release = installer.select_release(
            f"{'a' * 40}\trefs/tags/5.9.9-release\n"
            f"{'b' * 40}\trefs/tags/5.10.0-release\n"
        )
        self.assertEqual(release.version, (5, 10, 0))
        self.assertEqual(release.commit, 'b' * 40)

    def test_uses_commit_of_annotated_tag(self):
        release = installer.select_release(
            f"{'a' * 40}\trefs/tags/5.7.2-release\n"
            f"{'b' * 40}\trefs/tags/5.7.2-release^{{}}\n"
        )
        self.assertEqual(release.commit, 'b' * 40)

    def test_excludes_previews_other_majors_and_malformed_refs(self):
        refs = [
            '5.99.0-preview', '5.99.0-early-access', '6.0.0-release',
            '4.27.2-release', '5.07.0-release', '5.7.00-release',
        ]
        text = ''.join(f"{'a' * 40}\trefs/tags/{tag}\n" for tag in refs)
        text += f"{'c' * 40}\trefs/tags/5.6.3-release\n"
        self.assertEqual(installer.select_release(text).version, (5, 6, 3))

    def test_rejects_missing_valid_release(self):
        with self.assertRaises(ValueError):
            installer.select_release('not-a-sha refs/tags/5.7.0-release')

    def test_rejects_conflicting_refs(self):
        with self.assertRaises(ValueError):
            installer.select_release(
                f"{'a' * 40}\trefs/tags/5.7.0-release\n"
                f"{'b' * 40}\trefs/tags/5.7.0-release\n"
            )

    def test_ignores_peeled_ref_without_tag_object(self):
        with self.assertRaises(ValueError):
            installer.select_release(f"{'a' * 40}\trefs/tags/5.7.0-release^{{}}")


class SourceInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ue-bootstrap-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'fixture-source'
        self.source.mkdir()
        self.git('init', '-q', '--initial-branch=main')
        self.metadata = self.source / 'Engine/Build/Build.version'
        self.metadata.parent.mkdir(parents=True)
        self.metadata.write_text(json.dumps({
            'MajorVersion': 5, 'MinorVersion': 7, 'PatchVersion': 2,
        }), encoding='utf-8')
        self.git('add', 'Engine/Build/Build.version')
        self.git('-c', 'user.name=Bootstrap Test', '-c',
                 'user.email=bootstrap-test@example.invalid', 'commit', '-qm', 'Test metadata')
        self.git('-c', 'user.name=Bootstrap Test', '-c',
                 'user.email=bootstrap-test@example.invalid',
                 'tag', '-a', '5.7.2-release', '-m', 'Test release')
        self.sha = self.git('rev-parse', 'HEAD')
        self.release = installer.Release((5, 7, 2), '5.7.2-release', self.sha)

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.source, check=True,
                              text=True, capture_output=True).stdout.strip()

    def test_discovers_clones_and_verifies_local_fixture(self):
        destination = self.root / 'installed-source'
        with patch.object(installer, 'REMOTE', str(self.source)):
            release = installer.discover_release()
            self.assertEqual(release, self.release)
            self.assertEqual(installer.install_release(destination, release), destination)
        installer.verify_engine(destination, self.release)
        manifest = json.loads((destination / '.git/codex-unreal-install.json').read_text())
        self.assertEqual(manifest['commit'], self.sha)
        self.assertEqual(manifest['tag'], '5.7.2-release')
        self.assertEqual(list(self.root.glob('.installed-source.download-*')), [])

    def test_rejects_incorrect_commit(self):
        wrong = installer.Release((5, 7, 2), '5.7.2-release', 'a' * 40)
        with self.assertRaisesRegex(RuntimeError, 'commit'):
            installer.verify_engine(self.source, wrong)

    def test_rejects_incorrect_version_metadata(self):
        self.metadata.write_text('{"MajorVersion":5,"MinorVersion":7,"PatchVersion":1}')
        with self.assertRaisesRegex(RuntimeError, 'version'):
            installer.verify_engine(self.source, self.release)

    def test_preserves_existing_destination(self):
        destination = self.root / 'existing'
        destination.mkdir()
        marker = destination / 'user-file.txt'
        marker.write_text('preserve me')
        with self.assertRaises(FileExistsError):
            installer.install_release(destination, self.release)
        self.assertEqual(marker.read_text(), 'preserve me')

    def test_rejects_non_object_version_metadata(self):
        self.metadata.write_text('[5, 7, 2]')
        with self.assertRaisesRegex(RuntimeError, 'JSON object'):
            installer.verify_engine(self.source, self.release)

    def test_preserves_existing_empty_destination(self):
        destination = self.root / 'existing'
        destination.mkdir()
        with self.assertRaises(FileExistsError):
            installer.install_release(destination, self.release)
        self.assertTrue(destination.is_dir())

    def test_rejects_dangling_symlink_destination(self):
        destination = self.root / 'symlink'
        destination.symlink_to(self.root / 'missing-target', target_is_directory=True)
        with self.assertRaises(FileExistsError):
            installer.install_release(destination, self.release)
        self.assertTrue(destination.is_symlink())

    def test_rejects_installation_inside_project(self):
        with self.assertRaises(ValueError):
            installer.install_release(installer.PROJECT_ROOT / 'UnrealEngine', self.release)

    def test_cleans_only_own_staging_directory_after_failed_clone(self):
        marker = self.root / 'user-file.txt'
        marker.write_text('preserve me')
        destination = self.root / 'failed-install'
        with patch.object(installer, '_git', side_effect=RuntimeError('Access denied')):
            with self.assertRaises(RuntimeError):
                installer.install_release(destination, self.release)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob('.failed-install.download-*')), [])
        self.assertEqual(marker.read_text(), 'preserve me')

    def test_wrong_commit_never_publishes_destination(self):
        destination = self.root / 'wrong-commit'
        wrong = installer.Release((5, 7, 2), '5.7.2-release', 'a' * 40)
        with patch.object(installer, 'REMOTE', str(self.source)):
            with self.assertRaises(RuntimeError):
                installer.install_release(destination, wrong)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob('.wrong-commit.download-*')), [])

    def test_explicit_fork_is_used_and_recorded(self):
        fork = 'https://github.com/MikeDudikov/UnrealEngine.git'
        real_git = installer._git

        def fixture_git(*args, cwd=None):
            return real_git(*(str(self.source) if arg == fork else arg for arg in args), cwd=cwd)

        destination = self.root / 'fork-source'
        with patch.object(installer, '_git', side_effect=fixture_git) as git:
            release = installer.discover_release(fork)
            installer.install_release(destination, release, fork)
        self.assertIn(fork, git.call_args_list[0].args)
        manifest = json.loads((destination / '.git/codex-unreal-install.json').read_text())
        self.assertEqual(manifest['remote'], fork)
        self.assertEqual(manifest['commit'], self.sha)
        self.assertEqual(manifest['source_kind'], 'stable-tag')

    def test_invalid_repository_never_creates_install_directory(self):
        destination = self.root / 'invalid-repository'
        with patch.object(installer, '_git') as git, self.assertRaises(ValueError):
            installer.install_release(destination, self.release, 'https://other.invalid/owner/repo')
        git.assert_not_called()
        self.assertFalse(destination.exists())

    def test_discovers_and_installs_explicit_branch_snapshot(self):
        destination = self.root / 'snapshot-source'
        with patch.object(installer, 'REMOTE', str(self.source)):
            snapshot = installer.discover_snapshot(None, 'main')
            self.assertEqual(snapshot, installer.SourceSnapshot('refs/heads/main', self.sha))
            self.assertEqual(installer.install_snapshot(destination, snapshot), destination)
        manifest = json.loads((destination / '.git/codex-unreal-install.json').read_text())
        self.assertEqual(manifest['source_kind'], 'snapshot')
        self.assertEqual(manifest['ref'], 'refs/heads/main')
        self.assertEqual(manifest['commit'], self.sha)
        self.assertEqual(manifest['version'], [5, 7, 2])
        self.assertNotIn('tag', manifest)

    def test_snapshot_resolves_annotated_tag_and_exact_sha(self):
        with patch.object(installer, 'REMOTE', str(self.source)):
            tag_snapshot = installer.discover_snapshot(None, 'refs/tags/5.7.2-release')
            self.assertEqual(tag_snapshot.commit, self.sha)
            sha_snapshot = installer.discover_snapshot(None, self.sha)
            self.assertEqual(sha_snapshot, installer.SourceSnapshot(self.sha, self.sha))

    def test_snapshot_rejects_missing_and_ambiguous_refs(self):
        self.git('branch', '5.7.2-release')
        with patch.object(installer, 'REMOTE', str(self.source)):
            for ref in ['missing-branch', '5.7.2-release']:
                with self.subTest(ref=ref), self.assertRaises(ValueError):
                    installer.discover_snapshot(None, ref)

    def test_snapshot_rejects_non_ue5_source_before_publication(self):
        self.metadata.write_text('{"MajorVersion":6,"MinorVersion":0,"PatchVersion":0}')
        self.git('add', 'Engine/Build/Build.version')
        self.git('-c', 'user.name=Bootstrap Test', '-c',
                 'user.email=bootstrap-test@example.invalid', 'commit', '-qm', 'Non UE5 fixture')
        destination = self.root / 'invalid-snapshot'
        with patch.object(installer, 'REMOTE', str(self.source)):
            snapshot = installer.discover_snapshot(None, 'main')
            with self.assertRaisesRegex(RuntimeError, 'UE5'):
                installer.install_snapshot(destination, snapshot)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob('.invalid-snapshot.download-*')), [])

    def test_missing_tags_do_not_silently_select_a_branch(self):
        with patch.object(installer, '_git', return_value='') as git:
            with self.assertRaisesRegex(ValueError, 'no branch fallback'):
                installer.discover_release('https://github.com/MikeDudikov/UnrealEngine')
        self.assertEqual(git.call_count, 1)

    def test_invalid_snapshot_ref_is_rejected_without_git(self):
        for ref in ['--upload-pack=bad', '../main', 'refs/heads/a..b', 'refs/heads/a.lock', 'refs/heads/a//b']:
            with self.subTest(ref=ref), patch.object(installer, '_git') as git:
                with self.assertRaises(ValueError):
                    installer.discover_snapshot(None, ref)
                git.assert_not_called()

    def test_atomic_publish_does_not_replace_concurrently_created_directory(self):
        source = self.root / 'staged'
        source.mkdir()
        destination = self.root / 'concurrent'
        destination.mkdir()
        with self.assertRaises(FileExistsError):
            installer._rename_without_overwrite(source, destination)
        self.assertTrue(source.is_dir())
        self.assertTrue(destination.is_dir())


class CommandLineTests(unittest.TestCase):
    def test_explicit_fork_argument_is_forwarded_without_upstream_claim(self):
        release = installer.Release((5, 7, 2), '5.7.2-release', 'a' * 40)
        output = io.StringIO()
        fork = 'https://github.com/MikeDudikov/UnrealEngine.git'
        with patch.object(installer, 'discover_release', return_value=release) as discover, \
             patch.object(installer, 'install_release') as install, \
             contextlib.redirect_stdout(output):
            self.assertEqual(installer.main(['--check-access', '--repository', fork.removesuffix('.git')]), 0)
        discover.assert_called_once_with(fork)
        install.assert_not_called()
        self.assertIn('upstream is NOT verified', output.getvalue())
        self.assertIn(fork, output.getvalue())

    def test_explicit_snapshot_cli_does_not_discover_stable_release(self):
        fork = 'https://github.com/MikeDudikov/UnrealEngine.git'
        snapshot = installer.SourceSnapshot('refs/heads/release', 'a' * 40)
        output = io.StringIO()
        with patch.object(installer, 'discover_snapshot', return_value=snapshot) as discover, \
             patch.object(installer, 'discover_release') as stable, \
             patch.object(installer, 'install_snapshot') as install, \
             contextlib.redirect_stdout(output):
            self.assertEqual(installer.main(['--check-access', '--repository', fork, '--ref', 'release']), 0)
        discover.assert_called_once_with(fork, 'release')
        stable.assert_not_called()
        install.assert_not_called()
        self.assertIn('latest upstream version is NOT verified', output.getvalue())

    def test_rejected_repository_does_not_echo_credentials(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(installer, 'discover_release') as discover, \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = installer.main(['--repository', 'https://user:example-password@github.com/owner/repo'])
        self.assertEqual(code, 1)
        discover.assert_not_called()
        self.assertNotIn('example-password', output.getvalue() + errors.getvalue())

    def test_access_check_does_not_install(self):
        release = installer.Release((5, 7, 2), '5.7.2-release', 'a' * 40)
        with patch.object(installer, 'discover_release', return_value=release), \
             patch.object(installer, 'install_release') as install, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(installer.main(['--check-access']), 0)
        install.assert_not_called()

    def test_failed_access_returns_failure_without_installation(self):
        error_output = io.StringIO()
        with patch.object(installer, 'discover_release', side_effect=RuntimeError('Access denied')), \
             patch.object(installer, 'install_release') as install, \
             contextlib.redirect_stderr(error_output):
            self.assertEqual(installer.main([]), 1)
        install.assert_not_called()
        self.assertIn('Installation stopped', error_output.getvalue())


if __name__ == '__main__':
    unittest.main()
