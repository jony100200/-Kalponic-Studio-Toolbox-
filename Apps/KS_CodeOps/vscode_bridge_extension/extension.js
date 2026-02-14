const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

function bridgePath() {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    return undefined;
  }
  return path.join(folder.uri.fsPath, '.ks_codeops', 'bridge', 'latest_response.txt');
}

function ensureParent(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function activate(context) {
  const writeClipboard = vscode.commands.registerCommand('ksCodeOpsBridge.writeClipboardToBridge', async () => {
    const outputPath = bridgePath();
    if (!outputPath) {
      vscode.window.showErrorMessage('KS CodeOps Bridge: open a workspace folder first.');
      return;
    }

    const clip = await vscode.env.clipboard.readText();
    if (!clip || !clip.trim()) {
      vscode.window.showWarningMessage('KS CodeOps Bridge: clipboard is empty.');
      return;
    }

    const payload = `# captured_at: ${new Date().toISOString()}\n\n${clip}`;
    ensureParent(outputPath);
    fs.writeFileSync(outputPath, payload, { encoding: 'utf8' });
    vscode.window.showInformationMessage('KS CodeOps Bridge: clipboard written to bridge file.');
  });

  const openBridgeFile = vscode.commands.registerCommand('ksCodeOpsBridge.openBridgeFile', async () => {
    const outputPath = bridgePath();
    if (!outputPath) {
      vscode.window.showErrorMessage('KS CodeOps Bridge: open a workspace folder first.');
      return;
    }
    ensureParent(outputPath);
    if (!fs.existsSync(outputPath)) {
      fs.writeFileSync(outputPath, '', { encoding: 'utf8' });
    }
    const uri = vscode.Uri.file(outputPath);
    const doc = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(doc, { preview: false });
  });

  context.subscriptions.push(writeClipboard, openBridgeFile);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
