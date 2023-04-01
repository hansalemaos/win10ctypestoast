import argparse
import os
import sys
import pystray
from time import sleep as sleep_
from math import floor
from PIL import Image, ImageDraw
import subprocess
import threading
from functools import partial


def callback_func(pid):
    try:
        Popen(f"taskkill /F /PID {pid} /T")
    except Exception:
        pass


def timer_thread(timer, pid):
    timer.start()
    timer.join()
    callback_func(pid)


class Popen(subprocess.Popen):
    def __init__(
        self,
        args,
        bufsize=-1,
        executable=None,
        stdin=None,
        stdout=None,
        stderr=None,
        preexec_fn=None,
        close_fds=True,
        shell=False,
        cwd=None,
        env=None,
        universal_newlines=None,
        startupinfo=None,
        creationflags=0,
        restore_signals=True,
        start_new_session=False,
        pass_fds=(),
        *,
        group=None,
        extra_groups=None,
        user=None,
        umask=-1,
        encoding=None,
        errors=None,
        text=None,
        pipesize=-1,
        process_group=None,
        **kwargs,
    ):
        stdin = subprocess.PIPE
        stdout = subprocess.PIPE
        universal_newlines = False
        stderr = subprocess.PIPE
        # shell = False
        startupinfo = subprocess.STARTUPINFO()
        creationflags = 0 | subprocess.CREATE_NO_WINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        hastimeout = "timeout" in kwargs
        timeout = 0
        if hastimeout:
            timeout = kwargs["timeout"]

            del kwargs["timeout"]

        super().__init__(
            args,
            bufsize=bufsize,
            executable=executable,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            preexec_fn=preexec_fn,
            close_fds=close_fds,
            shell=shell,
            cwd=cwd,
            env=env,
            universal_newlines=universal_newlines,
            startupinfo=startupinfo,
            creationflags=creationflags,
            restore_signals=restore_signals,
            start_new_session=start_new_session,
            pass_fds=pass_fds,
            group=group,
            extra_groups=extra_groups,
            user=user,
            umask=umask,
            encoding=encoding,
            errors=errors,
            text=text,
            **kwargs,
        )
        if hastimeout:
            timer = threading.Timer(timeout, partial(callback_func, self.pid))
            timer.start()
        self.stdout_lines = []
        self.stderr_lines = []
        self._stdout_reader = StreamReader(self.stdout, self.stdout_lines)
        self._stderr_reader = StreamReader(self.stderr, self.stderr_lines)
        stdo = self._stdout_reader.start()
        stdee = self._stderr_reader.start()
        for stdo_ in stdo:
            self.stdout_lines.append(stdo_)
        for stde_ in stdee:
            self.stderr_lines.append(stde_)

        if hastimeout:
            try:
                timer.cancel()
            except Exception:
                pass
        self.stdout = b"".join(self.stdout_lines)
        self.stderr = b"".join(self.stderr_lines)

    def __exit__(self, *args, **kwargs):
        try:
            self._stdout_reader.stop()
            self._stderr_reader.stop()
        except Exception as fe:
            pass

        super().__exit__(*args, **kwargs)

    def __del__(self, *args, **kwargs):
        try:
            self._stdout_reader.stop()
            self._stderr_reader.stop()
        except Exception as fe:
            pass
        super().__del__(*args, **kwargs)


class StreamReader:
    def __init__(self, stream, lines):
        self._stream = stream
        self._lines = lines
        self._stopped = False

    def start(self):
        while not self._stopped:
            line = self._stream.readline()
            if not line:
                break
            yield line

    def stop(self):
        self._stopped = True


def sleep(secs):
    if secs == 0:
        return
    maxrange = 50 * secs
    if isinstance(maxrange, float):
        sleeplittle = floor(maxrange)
        sleep_((maxrange - sleeplittle) / 50)
        maxrange = int(sleeplittle)
    if maxrange > 0:
        for _ in range(maxrange):
            sleep_(0.016)


def show_tr(icon, title, msg, duration):
    icon.visible = True
    icon.notify(title, msg)
    sleep(duration)
    try:
        icon.remove_notification()
    except Exception as fe:
        pass

    try:
        icon.stop()
    except Exception as fe:
        pass


def create_image(width, height, color1, color2):
    image = Image.new("RGB", (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)

    return image


class ToastNotifier(object):
    def __init__(self):
        self.image = None
        self.icon = None

    def show_toast(
        self,
        title,
        msg,
        icon_path,
        duration=5.0,
        threaded=False,
        repeat=5,
        pause=1.0,
    ):
        if not icon_path:
            self.image = create_image(
                width=128, height=128, color1="red", color2="green"
            )
        else:
            self.image = Image.open(icon_path)
        for r in range(repeat):
            self.icon = pystray.Icon(title, self.image, msg)
            show_tr(self.icon, title, msg, duration)
            if threaded:
                self.icon.run_detached()
            else:
                self.icon.run()
            sleep(pause)
        if __name__ == "__main__":
            try:
                sys.exit()
            finally:
                os._exit(0)


def show_toast(title, message, icon="", duration=1, repeat=2, pause=1, threaded=False):
    sht = lambda: Popen(
        [
            sys.executable,
            __file__,
            "--title",
            str(title),
            "--message",
            str(message),
            "--icon",
            icon,
            "--duration",
            str(duration),
            "--repeat",
            str(repeat),
            "--pause",
            str(pause),
        ],
        timeout=(repeat * duration) + (repeat * pause),
        shell=False,
    )
    if not threaded:
        p2 = sht()
    else:
        timer = threading.Thread(target=sht)
        timer.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=28)
    )

    parser.add_argument(
        "--title",
        default="Notification",
        help="Notification title",
    )
    parser.add_argument(
        "--message",
        default="Message",
        help="Message",
    )
    parser.add_argument(
        "--icon",
        default="",
        help="Icon path",
    )
    parser.add_argument(
        "--duration",
        default=1.0,
        help="Visible for n seconds",
    )
    parser.add_argument(
        "--repeat",
        default=3,
        help="Show the message n times",
    )
    parser.add_argument(
        "--pause",
        default=1.0,
        help="Pause between repeating",
    )

    args = parser.parse_args()
    title = str(args.title)
    message = str(args.message)
    icon = str(args.icon)
    if not icon.strip():
        icon = None
    else:
        if not os.path.exists(icon):
            icon=None
    duration = float(args.duration)
    repeat = int(args.repeat)
    pause = float(args.pause)
    to = ToastNotifier()
    to.show_toast(
        title=title,
        msg=message,
        icon_path=icon,
        duration=duration,
        threaded=True,
        repeat=repeat,
        pause=pause,
    )
