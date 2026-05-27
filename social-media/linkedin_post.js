#!/usr/bin/env node
/**
 * LinkedIn image-upload + post script for CCN Social Hub.
 * Called by n8n Execute Command node. Reads post data from env vars.
 * Uses built-in fetch (Node 18+) — no npm packages required.
 *
 * Steps: register upload slot → download image → upload → post article
 */

const fs   = require('fs');
const path = require('path');

const MEMBER_ID = '41q6-gkeGG';
const LI_API    = 'https://api.linkedin.com';

function loadEnv() {
  // Prefer process.env (set on Docker container) over .env file
  if (process.env['LINKEDIN_ACCESS_TOKEN']) return process.env;
  const env = {};
  const raw = fs.readFileSync('/root/.hermes/.env', 'utf8');
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue;
    const eqIdx = trimmed.indexOf('=');
    const k = trimmed.slice(0, eqIdx).trim();
    const v = trimmed.slice(eqIdx + 1).trim();
    env[k] = v;
  }
  return env;
}

function liHeaders(token, contentType = 'application/json') {
  return {
    'Authorization': `Bearer ${token}`,
    'LinkedIn-Version': '202507',
    'X-Restli-Protocol-Version': '2.0.0',
    'Content-Type': contentType,
  };
}

async function registerImage(token) {
  const res = await fetch(`${LI_API}/rest/images?action=initializeUpload`, {
    method: 'POST',
    headers: liHeaders(token),
    body: JSON.stringify({ initializeUploadRequest: { owner: `urn:li:person:${MEMBER_ID}` } }),
  });
  if (!res.ok) throw new Error(`Register failed: ${res.status} ${await res.text()}`);
  const data = await res.json();
  return { uploadUrl: data.value.uploadUrl, imageUrn: data.value.image };
}

async function downloadImage(imageUrl) {
  const res = await fetch(imageUrl);
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const buf = await res.arrayBuffer();
  return Buffer.from(buf);
}

async function uploadImage(token, uploadUrl, imageBuffer) {
  const res = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'image/jpeg',
    },
    body: imageBuffer,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status} ${await res.text()}`);
}

async function postArticle(token, { message, postUrl, title, subtitle }) {
  const mediaItem = {
    status: 'READY',
    originalUrl: postUrl,
    title: { text: title },
    description: { text: subtitle || '' },
  };

  const body = {
    author: `urn:li:person:${MEMBER_ID}`,
    lifecycleState: 'PUBLISHED',
    specificContent: {
      'com.linkedin.ugc.ShareContent': {
        shareCommentary: { text: message },
        shareMediaCategory: 'ARTICLE',
        media: [mediaItem],
      },
    },
    visibility: {
      'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC',
    },
  };

  const bodyStr = JSON.stringify(body);
  process.stderr.write(JSON.stringify({
    debug: 'postArticle body',
    commentary: message,
    commentaryLength: message.length,
    bodyLength: bodyStr.length,
  }) + '\n');

  const res = await fetch(`${LI_API}/v2/ugcPosts`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Restli-Protocol-Version': '2.0.0',
      'Content-Type': 'application/json',
    },
    body: bodyStr,
  });
  if (!res.ok) throw new Error(`Post failed: ${res.status} ${await res.text()}`);
  const data = await res.json();
  return data.id || '';
}

async function main() {
  const env   = loadEnv();
  const token = env['LINKEDIN_ACCESS_TOKEN'];

  let title, subtitle, postUrl, message;

  if (process.env['CCN_PAYLOAD']) {
    // JSON payload from n8n Execute Command — handles newlines + special chars safely
    const p = JSON.parse(Buffer.from(process.env['CCN_PAYLOAD'], 'base64').toString('utf8'));
    title    = p.title    || 'New from CCN';
    subtitle = p.subtitle || '';
    postUrl  = p.url      || 'https://danova.substack.com';
    // Use explicit message field; never fall back silently (would drop hashtags)
    if (!p.message) throw new Error('CCN_PAYLOAD missing message field');
    message  = p.message;
  } else {
    title    = process.env['LI_TITLE']     || 'New from CCN';
    subtitle = process.env['LI_SUBTITLE']  || '';
    postUrl  = process.env['LI_URL']       || 'https://danova.substack.com';
    message  = process.env['LI_MESSAGE']   || title;
  }

  process.stderr.write(JSON.stringify({
    debug: 'linkedin_post.js received',
    title,
    messagePreview: message.slice(0, 80) + (message.length > 80 ? '…' : ''),
    messageLength: message.length,
    hasHashtags: message.includes('#'),
  }) + '\n');

  const postId = await postArticle(token, { message, postUrl, title, subtitle });
  process.stdout.write(JSON.stringify({ linkedInPostId: postId, success: true }) + '\n');
}

main().catch(err => {
  process.stderr.write(JSON.stringify({ error: err.message }) + '\n');
  process.exit(1);
});
