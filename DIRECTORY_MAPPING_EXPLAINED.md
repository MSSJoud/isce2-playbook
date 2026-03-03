# Docker Directory Mapping Explained

## 🗺️ Where is `/workspace/` defined?

**Defined in:** `docker-compose.yml` (line 7)

```yaml
services:
  isce2-insar:
    working_dir: /workspace
    volumes:
      - ./:/workspace                        # ← HERE!
      - /mnt/data/tokyo_test:/mnt/data/tokyo_test
```

## 📂 Directory Mapping Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    HOST SYSTEM (Ubuntu)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  /home/ubuntu/work/isce2-playbook/  ←──┐                    │
│  ├── docker-compose.yml                 │                    │
│  ├── input-files/                       │                    │
│  │   └── topsApp_with_unwrap.xml        │                    │
│  ├── merged/              ←─────────────┼──── OUTPUT HERE   │
│  │   ├── filt_topophase.flat            │                    │
│  │   ├── phsig.cor                      │                    │
│  │   └── [unwrapped files go here]      │                    │
│  ├── coarse_coreg/                      │                    │
│  ├── fine_coreg/                        │                    │
│  ├── reference/                         │                    │
│  ├── secondary/                         │                    │
│  └── isce.log                           │                    │
│                                          │                    │
│  /mnt/data/tokyo_test/      ←──┐        │                    │
│  └── output/                    │        │                    │
│      ├── S1A_*.zip (raw data)  │        │                    │
│      └── orbit files            │        │                    │
│                                 │        │                    │
└─────────────────────────────────┼────────┼────────────────────┘
                                  │        │
                    ══════════════╧════════╧═══════════════
                              Docker Volume Mapping
                    ═══════════════════════════════════════
                                  ▼        ▼
┌─────────────────────────────────────────────────────────────┐
│              DOCKER CONTAINER (isce2-insar)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  /workspace/                    ←──── MAPPED FROM HOST       │
│  ├── input-files/                                            │
│  │   └── topsApp_with_unwrap.xml                            │
│  ├── merged/                    ←──── OUTPUTS WRITTEN HERE  │
│  ├── coarse_coreg/                                           │
│  ├── fine_coreg/                                             │
│  └── isce.log                                                │
│                                                               │
│  /mnt/data/tokyo_test/          ←──── MAPPED FROM HOST       │
│  └── output/                                                 │
│                                                               │
│  /opt/isce2/                    ←──── ISCE2 SOFTWARE         │
│  └── [ISCE2 binaries]                  (inside container)    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 Key Points

### 1. `/workspace/` = The Project Directory
```bash
/workspace/                      (inside Docker)
    ↕
/home/ubuntu/work/isce2-playbook/  (on your host)
```

**Both paths point to the SAME location** - files written in the container appear on your host!

### 2. NOT `/work/isce2_src`
❌ `/work/isce2_src` does **NOT exist** in your setup
❌ This might be from example documentation or another project
✅ The actual path is: `/home/ubuntu/work/isce2-playbook/`

### 3. Where Outputs Go

When you run:
```bash
docker compose run --rm isce2-insar topsApp.py /workspace/input-files/topsApp_with_unwrap.xml
```

**All outputs write to:**
- Inside container: `/workspace/merged/filt_topophase.unw`
- On your host: `/home/ubuntu/work/isce2-playbook/merged/filt_topophase.unw`

**Same file, two paths!** 🎯

## 📍 Current File Locations

### Already Exist (from previous processing):
```
/home/ubuntu/work/isce2-playbook/
├── merged/
│   ├── filt_topophase.flat        ✅ 17 MB (wrapped phase)
│   ├── filt_topophase.flat.geo    ✅ 232 MB (geocoded)
│   ├── phsig.cor                  ✅ 8.3 MB (coherence)
│   ├── topophase.cor              ✅ 17 MB (correlation)
│   └── los.rdr                    ✅ 17 MB (line-of-sight)
├── coarse_coreg/                  ✅ (coregistration done)
└── fine_coreg/                    ✅ (fine alignment done)
```

### Will be Created (after unwrapping):
```
/home/ubuntu/work/isce2-playbook/
└── merged/
    ├── filt_topophase.unw         🔜 ~50 MB (UNWRAPPED phase)
    ├── filt_topophase.unw.conncomp 🔜 ~17 MB (connected components)
    ├── filt_topophase.unw.geo     🔜 ~500 MB (geocoded unwrapped)
    └── phsig.cor.geo              ✅ Already exists (116 MB)
```

## ✅ Can Option 2 Be Used?

**YES!** The repository has all the required files:

```bash
# Option 2: Resume from existing processing
cd /home/ubuntu/work/isce2-playbook
docker compose run --rm isce2-insar topsApp.py \
    /workspace/input-files/topsApp_with_unwrap.xml \
    --start=unwrap
```

### Why Option 2 Works:
✅ `filt_topophase.flat` exists (filtered interferogram)
✅ `phsig.cor` exists (coherence for unwrapping)
✅ All coregistration complete (coarse_coreg, fine_coreg)
✅ No errors in isce.log
✅ Processing stopped before unwrap step

### Processing Time:
- **Unwrap step alone:** ~15-30 minutes
- **Plus geocoding:** +5-10 minutes
- **Total:** ~20-40 minutes (vs 60-90 min for full reprocessing)

## 🌐 Volume Mapping Details

From `docker-compose.yml`:

```yaml
volumes:
  - /home/ubuntu/.netrc:/root/.netrc              # Credentials
  - ./:/workspace                                  # Project directory
  - /mnt/data/tokyo_test:/mnt/data/tokyo_test     # Data storage
```

### What Each Mapping Does:

1. **`./:/workspace`**
   - `.` = current directory when you run docker compose
   - Since you're in `/home/ubuntu/work/isce2-playbook/`, that becomes `/workspace`
   - **Bidirectional:** Changes in container appear on host and vice versa

2. **`/mnt/data/tokyo_test:/mnt/data/tokyo_test`**
   - External data storage (your downloaded Sentinel-1 files)
   - Same path in container and host for simplicity
   - Read-only access during processing

3. **`/home/ubuntu/.netrc:/root/.netrc`**
   - ASF/NASA credentials for data download
   - Maps your host credentials to container root user

## 🔍 Verify Mappings

```bash
# From HOST - check files
ls -lh /home/ubuntu/work/isce2-playbook/merged/ | head

# From DOCKER - see same files!
docker compose run --rm isce2-insar ls -lh /workspace/merged/ | head

# They show IDENTICAL content! ✅
```

## 📊 Output File Summary

After unwrapping completes, you'll have:

| File | Host Path | Docker Path | Size | Description |
|------|-----------|-------------|------|-------------|
| Unwrapped phase | `/home/ubuntu/work/isce2-playbook/merged/filt_topophase.unw` | `/workspace/merged/filt_topophase.unw` | ~50 MB | Continuous phase |
| Connected components | `.../merged/filt_topophase.unw.conncomp` | `/workspace/merged/filt_topophase.unw.conncomp` | ~17 MB | Quality mask |
| Geocoded unwrapped | `.../merged/filt_topophase.unw.geo` | `/workspace/merged/filt_topophase.unw.geo` | ~500 MB | Geographic coords |
| VRT files | `.../merged/*.vrt` | `/workspace/merged/*.vrt` | ~1 KB | GDAL pointers |

## 🚀 Ready to Run

The command from **Option 2**:

```bash
cd /home/ubuntu/work/isce2-playbook

docker compose run --rm isce2-insar topsApp.py \
    /workspace/input-files/topsApp_with_unwrap.xml \
    --start=unwrap
```

**What this does:**
1. Starts `isce2-insar` container
2. Mounts `/home/ubuntu/work/isce2-playbook/` as `/workspace/`
3. Reads config from `/workspace/input-files/topsApp_with_unwrap.xml`
4. Resumes processing at unwrap step (skips coregistration, interferogram)
5. Writes `.unw` files to `/workspace/merged/`
6. Exits when complete
7. Files remain on host in `/home/ubuntu/work/isce2-playbook/merged/`

## 📝 Monitoring

Watch progress:
```bash
# From another terminal
tail -f /home/ubuntu/work/isce2-playbook/isce.log

# Look for these steps:
# - "Running unwrap"
# - "SNAPHU processing"
# - "Geocoding unwrapped phase"
# - "Done."
```

Check outputs as they're created:
```bash
watch -n 5 'ls -lh /home/ubuntu/work/isce2-playbook/merged/*.unw* 2>/dev/null'
```

## ❓ FAQ

**Q: If I delete files in `/workspace/merged/` inside Docker, are they deleted on my host?**
A: **YES!** It's the same filesystem. Be careful.

**Q: Can I edit files on host while Docker is running?**
A: Yes, changes appear immediately in the container.

**Q: What if I want outputs in a different location?**
A: Edit docker-compose.yml volume mapping or use Option 3 from UNWRAPPING_GUIDE.md

**Q: Why not use `/work/isce2_src`?**
A: That path doesn't exist in your setup. It might be from:
- Different project
- Example documentation
- Older ISCE2 installation method

This setup uses `/home/ubuntu/work/isce2-playbook/` which is cleaner and project-specific.

---

**Bottom line:** Run Option 2, outputs go to `merged/` in your project directory, same place as existing files. No surprises! 🎉
