## Amazon Linux 2023: DNF Kernel Picker Plugin

Amazon Linux 2023 provides both 6.1 and 6.12 kernel packages.  Some of the kernel 6.12 related packages are namespaced, while others are not.

For example, the 6.12 kernel package is provided as `kernel6.12` (without a dash, as `kernel6.12-6.12.XXX.YYY` rather than `kernel-6.12.XXX.YYY`).

This is to prevent unintended major kernel upgrades.  On the other hand, non-namespaced packages can be updated as usual.

For example, if the 6.1 kernel and kernel-headers are installed,

```
$ uname -r
6.1.131-143.221.amzn2023.x86_64

$ rpm -q kernel kernel-headers
kernel-6.1.131-143.221.amzn2023.x86_64
kernel-headers-6.1.131-143.221.amzn2023.x86_64
```

and an update to kernel-headers is performed, the latest 6.12 version will be selected.

```
$ sudo dnf update kernel-headers
...
Upgrading:
 kernel-headers     x86_64     6.12.22-27.96.amzn2023     amazonlinux     1.5 M
```

With this plugin enabled, kernel-related package updates will be restricted to the specified major version.

```
$ sudo dnf update kernel-headers -v
...
Filtered packages
...
  kernel-headers-6.12.20.23.97.amzn2023.x86_64 (amazonlinux)
  kernel-headers-6.12.22.27.96.amzn2023.x86_64 (amazonlinux)
...
Upgrading:
 kernel-headers    x86_64    6.1.132-147.221.amzn2023      amazonlinux    1.4 M
```


### Plugin Usage:

`kernelpicker` is a subcommand for setting the preferred kernel variant.

```
$ dnf kernelpicker --help
usage: dnf kernelpicker [[6.12 | 6.1]]

  [6.12 | 6.1]          Set the preference for kernel package variant, or show it if not specified
```

If no argument is provided, it will display the current setting.

```
$ dnf kernelpicker
variant: 6.1
```

When an argument is provided, `kernelpicker` will update the setting,

```
$ sudo dnf kernelpicker 6.12
variant: 6.12
```

and subsequent DNF commands related to kernel packages will be restricted to the specified major version except for installed packages.

```
$ sudo dnf kernelpicker 6.1
variant: 6.1

#
# No 6.12 kernel in the result
#
$ sudo dnf list kernel-headers --showduplicates
Installed Packages
kernel-headers.x86_64           6.1.131-143.221.amzn2023            @amazonlinux
Available Packages
kernel-headers.x86_64           6.1.10-15.42.amzn2023               amazonlinux
...
kernel-headers.x86_64           6.1.132-147.221.amzn2023            amazonlinux

#
# No 6.1 kernel in the result except for the installed package
#
$ sudo dnf kernelpicker 6.12
variant: 6.12

$ sudo dnf list kernel-headers --showduplicates
Installed Packages
kernel-headers.x86_64           6.1.131-143.221.amzn2023            @amazonlinux
Available Packages
kernel-headers.x86_64           6.12.20-23.97.amzn2023              amazonlinux
kernel-headers.x86_64           6.12.22-27.96.amzn2023              amazonlinux
```