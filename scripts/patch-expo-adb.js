const fs = require('fs');
const path = require('path');

const targetPath = path.join(
  __dirname,
  '..',
  'node_modules',
  'expo',
  'node_modules',
  '@expo',
  'cli',
  'build',
  'src',
  'start',
  'platforms',
  'android',
  'adb.js'
);

if (!fs.existsSync(targetPath)) {
  process.exit(0);
}

let content = fs.readFileSync(targetPath, 'utf8');

const oldCode = "const props = line.split(' ').filter(Boolean);";
const newCode = `const stateMatch = line.match(/\\s+(device|offline|unauthorized|authorizing|connecting|recovery|sideload|bootloader)\\b/);
        let props;
        if (stateMatch && stateMatch.index !== undefined) {
            const pid = line.substring(0, stateMatch.index).trim();
            const status = stateMatch[1];
            const rest = line.substring(stateMatch.index + stateMatch[0].length).trim().split(/\\s+/).filter(Boolean);
            props = [pid, status, ...rest];
        } else {
            props = line.split(' ').filter(Boolean);
        }`;

if (content.includes(oldCode)) {
  content = content.replace(oldCode, newCode);
  fs.writeFileSync(targetPath, content, 'utf8');
  console.log('[patch-expo-adb] Successfully patched Expo CLI ADB parser for devices with spaces.');
} else {
  console.log('[patch-expo-adb] Expo CLI ADB parser is already patched.');
}
