package main

import (
	"bytes"
	"encoding/binary"
	"os"
	"path/filepath"
	"syscall"
	"time"
)

// Watch the directory so atomic renames remain observable. No idle stat loop.
// A bounded fallback preserves updates on filesystems without inotify.
func watchLiveState502(path string) {
	refresh := func() { if b, e := os.ReadFile(path); e == nil { liveHub.publish(b) } }
	for {
		fd, err := syscall.InotifyInit1(syscall.IN_CLOEXEC)
		if err == nil {
			_, err = syscall.InotifyAddWatch(fd, filepath.Dir(path), syscall.IN_CLOSE_WRITE|syscall.IN_MOVED_TO|syscall.IN_CREATE|syscall.IN_DELETE_SELF|syscall.IN_MOVE_SELF)
		}
		if err != nil {
			if fd >= 0 { syscall.Close(fd) }
			refresh()
			time.Sleep(500 * time.Millisecond)
			continue
		}
		refresh()
		buf := make([]byte, 4096)
		watching := true
		for watching {
			n, e := syscall.Read(fd, buf)
			if e == syscall.EINTR { continue }
			if e != nil || n == 0 { break }
			changed := false
			for off := 0; off+16 <= n; {
				mask := binary.LittleEndian.Uint32(buf[off+4:off+8])
				size := int(binary.LittleEndian.Uint32(buf[off+12:off+16]))
				if off+16+size > n { break }
				name := string(bytes.TrimRight(buf[off+16:off+16+size], "\x00"))
				if name == filepath.Base(path) || mask&syscall.IN_Q_OVERFLOW != 0 { changed = true }
				if mask&(syscall.IN_IGNORED|syscall.IN_DELETE_SELF|syscall.IN_MOVE_SELF) != 0 { watching = false }
				off += 16+size
			}
			if changed { refresh() }
		}
		syscall.Close(fd)
		time.Sleep(500 * time.Millisecond)
	}
}
