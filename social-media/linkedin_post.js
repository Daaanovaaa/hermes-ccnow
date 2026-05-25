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

async function postArticle(token, { message, postUrl, title, subtitle, imageUrn }) {
  const body = {
    author: `urn:li:person:${MEMBER_ID}`,
    commentary: message,
    visibility: 'PUBLIC',
    distribution: { feedDistribution: 'MAIN_FEED' },
    lifecycleState: 'PUBLISHED',
    isReshareDisabledByAuthor: false,
  };
  if (imageUrn) {
    body.content = {
      article: {
        source: postUrl,
        thumbnail: imageUrn,
        title,
        description: subtitle || '',
      },
    };
  }
  const res = await fetch(`${LI_API}/rest/posts`, {
    method: 'POST',
    headers: liHeaders(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Post failed: ${res.status} ${await res.text()}`);
  return res.headers.get('x-restli-id') || '';
}

async function main() {
  const env      = loadEnv();
  const token    = env['LINKEDIN_ACCESS_TOKEN'];
  const title    = process.env['LI_TITLE']     || 'New from CCN';
  const subtitle = process.env['LI_SUBTITLE']  || '';
  const postUrl  = process.env['LI_URL']       || 'https://danova.substack.com';
  const imageUrl = process.env['LI_IMAGE_URL'] || '';
  const message  = process.env['LI_MESSAGE']   || title;

  let imageUrn = null;

  if (imageUrl) {
    try {
      const { uploadUrl, imageUrn: urn } = await registerImage(token);
      const imageBuffer = await downloadImage(imageUrl);
      await uploadImage(token, uploadUrl, imageBuffer);
      imageUrn = urn;
    } catch (err) {
      process.stderr.write(JSON.stringify({ warning: `Image upload failed: ${err.message}, posting without image` }) + '\n');
    }
  }

  const postId = await postArticle(token, { message, postUrl, title, subtitle, imageUrn });
  process.stdout.write(JSON.stringify({ linkedInPostId: postId, imageUrn, success: true }) + '\n');
}

main().catch(err => {
  process.stderr.write(JSON.stringify({ error: err.message }) + '\n');
  process.exit(1);
});
