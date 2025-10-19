# Offensive Operations Artifacts - Chengyu Hu

## Specialization: Offensive Security Operations

This folder contains all offensive security testing artifacts developed by Chengyu Hu for penetration testing and vulnerability discovery in the Tatou PDF Watermarking Platform.

## Contents

### Reconnaissance Tools
- **recon_http.sh** - HTTP service reconnaissance script
- **scan_flask_ports.sh** - Flask application port scanning
- **flask_entry_finder.sh** - Flask entry point discovery
- **surface_scan.sh** - Attack surface enumeration
- **surface_report.txt** - Attack surface analysis results

### Reconnaissance Results
Located in `recon_out/` directory:
- Captured HTTP responses from multiple targets
- HTML page analysis (index, login, signup)
- Security headers inspection
- Service fingerprinting results

### Vulnerability Scanning
- **ssti_scanner.sh** - Server-Side Template Injection scanner
- **ssti_auto_probe_plus.sh** - Advanced SSTI detection with automated exploitation
- **lfi_hunt.py** - Local File Inclusion vulnerability hunter
- **lfi_report.txt** - LFI scanning results and findings

### Cryptographic Analysis
- **metadata_key_finder.py** - Cryptographic key extraction from metadata
- **aes_probe.py** - AES encryption analysis and key discovery
- **aes_probe_report.txt** - Detailed AES analysis findings
- **decode_probe.py** - Base64 and encoding analysis tool
- **decode_probe_report.txt** - Decoding analysis results
- **b64_analyzer.py** - Advanced Base64 pattern analysis

### Data Extraction
- **key_hints.txt** - Discovered cryptographic key hints
- **candidates.txt** - Potential key candidates
- **aes_candidates.txt** - AES key candidates
- **base64_blobs.txt** - Extracted Base64-encoded data
- **urls_found.txt** - Discovered URLs and endpoints
- **targets.txt** - Target list for testing

### PDF Security Analysis
Located in `pdfs/` directory:
- **scan_all_pdfs_v45.py** - Comprehensive PDF security scanner
- **pdf_sanitize.py** - PDF metadata sanitization tool
- **ultimate_cleaner.py** - Advanced PDF cleaning utility
- **safe_watermark_clean.py** - Safe watermark removal testing
- **verify_cleanliness.sh** - PDF sanitization verification

#### PDF Metadata Tools
- **purge_info_g13.py** - PDF info dictionary purging
- **hard_purge_info_g13.py** - Aggressive metadata removal
- **purge_xmp_g10.py** - XMP metadata removal
- **rebuild_clean_g13.py** - Clean PDF rebuilding
- **redact_overlay_g19.py** - Redaction overlay testing

#### Cleaning Reports
- Multiple audit reports documenting cleaning operations
- `cleaned_safe/` and `cleaned_struct/` - Cleaned PDF outputs

### Signature and Verification
- **sign.py** - Digital signature testing
- **signature.txt** - Signature analysis results
- **verify_g13.sh** - Signature verification script
- **verify_g13_plus.sh** - Enhanced verification with bypass attempts

### Git Security
- **git_leak_scan.sh** - Git repository secret scanning
- **git_leak_report.txt** - Discovered secrets and sensitive data

### Reporting
- **scan_report.txt** - Comprehensive security scan results

## Testing Methodology

### Phase 1: Reconnaissance
1. **Service Discovery**
   - Port scanning and service enumeration
   - HTTP endpoint discovery
   - Technology stack identification

2. **Attack Surface Mapping**
   - Entry point identification
   - Parameter discovery
   - Authentication mechanisms analysis

### Phase 2: Vulnerability Discovery
1. **Injection Testing**
   - Server-Side Template Injection (SSTI)
   - Local File Inclusion (LFI)
   - Command injection attempts

2. **Cryptographic Analysis**
   - Weak encryption detection
   - Key extraction attempts
   - Encoding/decoding analysis

3. **PDF Security Testing**
   - Watermark bypass attempts
   - Metadata leakage analysis
   - Sanitization verification

### Phase 3: Exploitation
1. **Proof of Concept Development**
   - Exploit script creation
   - Bypass technique validation
   - Impact assessment

2. **Data Extraction**
   - Sensitive data discovery
   - Cryptographic material extraction
   - Configuration file analysis

## Key Findings

### Vulnerabilities Discovered
1. **Cryptographic Issues**
   - Potential key disclosure in metadata
   - Weak random number generation patterns
   - Predictable encryption parameters

2. **Information Disclosure**
   - Verbose error messages
   - Debug information leakage
   - Git repository exposure

3. **PDF Security Concerns**
   - Metadata leakage risks
   - Watermark removal possibilities
   - Information hiding in PDF structure

4. **Web Application Issues**
   - SSTI vulnerability patterns
   - LFI attack vectors
   - Insufficient input validation

## Tools Developed

### Reconnaissance Suite
- Automated service discovery
- HTTP fingerprinting
- Attack surface mapping

### Exploitation Tools
- SSTI detection and exploitation
- LFI vulnerability scanner
- Cryptographic analysis utilities

### PDF Analysis Framework
- Metadata extraction and analysis
- Watermark bypass testing
- Sanitization verification

## Key Achievements

1. **Comprehensive Assessment**: Performed full-spectrum offensive security testing
2. **Tool Development**: Created custom tools for specific vulnerability classes
3. **Cryptographic Analysis**: Advanced analysis of encryption implementations
4. **PDF Security**: Deep dive into PDF security and watermarking techniques
5. **Documentation**: Detailed reporting of findings and methodologies

## Usage Examples

### Running Reconnaissance
```bash
# Scan target services
./scan_flask_ports.sh

# Enumerate attack surface
./surface_scan.sh http://target:5000

# HTTP reconnaissance
./recon_http.sh http://target:5000
```

### Vulnerability Scanning
```bash
# SSTI detection
./ssti_auto_probe_plus.sh

# LFI scanning
python lfi_hunt.py --target http://localhost:5000

# Cryptographic analysis
python aes_probe.py
python metadata_key_finder.py
```

### PDF Security Testing
```bash
# Scan PDF for security issues
python scan_all_pdfs_v45.py input.pdf

# Test sanitization
./verify_cleanliness.sh input.pdf

# Analyze metadata
python metadata_key_finder.py pdfs/
```

## Security Impact

The offensive operations discovered critical security issues that were subsequently fixed:
- Hardened cryptographic implementations
- Improved input validation
- Enhanced PDF metadata handling
- Removed information disclosure vectors

## Responsible Disclosure

All findings were responsibly disclosed to the development team and remediated before project completion.

## Contact
Chengyu Hu - Offensive Operations Specialization

