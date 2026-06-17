const https = require('https');
const crypto = require('crypto');

const playerUrl = process.argv[2];
if (!playerUrl) {
    console.error("Error: Player URL is required");
    process.exit(1);
}

function httpGet(apiUrl, referer) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(apiUrl);
        const options = {
            hostname: parsed.hostname,
            path: parsed.pathname + parsed.search,
            port: parsed.port,
            headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": referer,
            }
        };
        https.get(options, (res) => {
            if (res.statusCode !== 200) {
                reject(new Error(`HTTP Status ${res.statusCode}`));
                return;
            }
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => resolve(data));
        }).on('error', (err) => reject(err));
    });
}

async function main() {
    const parsedUrl = new URL(playerUrl);
    const hash = parsedUrl.hash || "";
    const id = hash.replace("#", "");
    if (!id) {
        throw new Error("No video ID found in player URL hash");
    }
    
    const apiUrl = `https://${parsedUrl.host}/api/v1/video?id=${id}`;
    const encryptedHex = await httpGet(apiUrl, "https://watchmmafull.com/");
    
    const key = Buffer.from("kiemtienmua911ca", "utf8");
    const iv = Buffer.from("1234567890oiuytr", "utf8");
    
    const ciphertext = Buffer.from(encryptedHex.trim(), 'hex');
    const decipher = crypto.createDecipheriv('aes-128-cbc', key, iv);
    decipher.setAutoPadding(true);
    let decrypted = decipher.update(ciphertext, null, 'utf8');
    decrypted += decipher.final('utf8');
    
    console.log(decrypted);
}

main().catch(err => {
    console.error(err.message);
    process.exit(1);
});
