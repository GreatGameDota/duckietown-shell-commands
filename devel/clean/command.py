import argparse
import io
import os
import subprocess

from dt_shell import DTCommandAbs, dtslogger, DTShell
from duckietown_docker_utils import ENV_REGISTRY

from utils.docker_utils import DEFAULT_MACHINE, get_endpoint_architecture, DEFAULT_REGISTRY, STAGING_REGISTRY
from utils.dtproject_utils import DTProject


class DTCommand(DTCommandAbs):
    help = "Removes the Docker images relative to the current project"

    @staticmethod
    def _parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-C",
            "--workdir",
            default=os.getcwd(),
            help="Directory containing the project to clean",
        )
        parser.add_argument(
            "-a",
            "--arch",
            default=None,
            help="Target architecture for the image to clean",
        )
        parser.add_argument(
            "-H",
            "--machine",
            default=DEFAULT_MACHINE,
            help="Docker socket or hostname where to clean the image",
        )
        parser.add_argument(
            "--stage",
            "--staging",
            dest="staging",
            action="store_true",
            default=False,
            help="Use staging environment",
        )
        parser.add_argument(
            "--registry",
            type=str,
            default=DEFAULT_REGISTRY,
            help="Use this Docker registry",
        )
        parsed, _ = parser.parse_known_args(args=args)
        return parsed

    @staticmethod
    def command(shell: DTShell, args, **kwargs):
        parsed = DTCommand._parse_args(args)
        if "parsed" in kwargs:
            parsed.__dict__.update(kwargs["parsed"].__dict__)
        # ---
        dtslogger.info("Project workspace: {}".format(parsed.workdir))

        # show info about project
        shell.include.devel.info.command(shell, args)
        project = DTProject(parsed.workdir)

        # staging
        if parsed.staging:
            parsed.registry = STAGING_REGISTRY
        else:
            # custom Docker registry
            docker_registry = os.environ.get(ENV_REGISTRY, DEFAULT_REGISTRY)
            if docker_registry != DEFAULT_REGISTRY:
                dtslogger.warning(f"Using custom {ENV_REGISTRY}='{docker_registry}'.")
                parsed.registry = docker_registry

        # registry
        if parsed.registry != DEFAULT_REGISTRY:
            dtslogger.info(f"Using custom registry: {parsed.registry}")

        # pick the right architecture if not set
        if parsed.arch is None:
            parsed.arch = get_endpoint_architecture(parsed.machine)
            dtslogger.info(f"Target architecture automatically set to {parsed.arch}.")
        # create defaults
        images = [project.image(parsed.arch, registry=parsed.registry, staging=parsed.staging)]
        # clean release version
        if project.is_release():
            images.append(
                project.image_release(parsed.arch, registry=parsed.registry, staging=parsed.staging)
            )
        # remove images
        for image in images:
            img = _run_cmd(["docker", "-H=%s" % parsed.machine, "images", "-q", image], get_output=True)
            if img:
                dtslogger.info("Removing image {}...".format(image))
                try:
                    _run_cmd(["docker", "-H=%s" % parsed.machine, "rmi", image])
                except RuntimeError:
                    dtslogger.warn(
                        "We had some issues removing the image '{:s}' on '{:s}'".format(image, parsed.machine)
                        + ". Just a heads up!"
                    )

    @staticmethod
    def complete(shell, word, line):
        return []


def _run_cmd(cmd, get_output=False, print_output=False):
    dtslogger.debug("$ %s" % cmd)
    if get_output:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        lines = []
        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            line = line.rstrip()
            if print_output:
                print(line)
            if line:
                lines.append(line)
        proc.wait()
        if proc.returncode != 0:
            msg = "The command {} returned exit code {}".format(cmd, proc.returncode)
            dtslogger.error(msg)
            raise RuntimeError(msg)
        return lines
    else:
        subprocess.check_call(cmd)
