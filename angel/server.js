const express = require('express');
const fs = require('fs');
const { chromium } = require('playwright');

const app = express();
const PORT = process.env.PORT || 3000;

// =========================
// KEYS SYSTEM
// =========================
function loadKeys() {
  return JSON.parse(fs.readFileSync('./keys.json'));
}
function saveKeys(data) {
  fs.writeFileSync('./keys.json', JSON.stringify(data, null, 2));
}

// =========================
// CLICK FUNCTIONS
// =========================
async function clickMultiple(page, selector, times = 1, waitAfter = 2000) {
  for (let i = 0; i < times; i++) {
    try {
      await page.click(selector, { timeout: 5000 });
      await page.waitForTimeout(waitAfter);
    } catch {}
  }
}

async function protectFromAds(page, allowedHost) {
  try {
    const currentHost = new URL(page.url()).hostname;
    if (currentHost !== allowedHost) {
      await page.goBack();
      await page.waitForTimeout(1000);
    }
  } catch {}
}

// =========================
// FLOWS (ADD MORE WEBSITES HERE)
// =========================
const flows = {
  "linkvertise.com": {
    steps: [
      { selector: "text=View a short ad", times: 1, waitAfter: 40000 },
      { selector: "text=X", times: 1 },
      { selector: "text=Get Link", times: 1 },
      { selector: "text=Watch Ads", times: 1 },
      { selector: "text=Continue", times: 1 },
      { selector: "text=Skip", times: 10 },
      { selector: "text=Open", times: 1 },
      { selector: "text=Copy", times: 1 }
    ]
  },
  "auth.platorelay.com": {
    steps: [
      { selector: "text=Continue", times: 1 },
      { selector: "text=Copy", times: 1 }
    ]
  },
  "loot-link.com": {
    steps: [
      { selector: 'text="?"', times: 10, waitAfter: 2000 },
      { selector: "text=UNLOCK CONTENT", times: 1 },
      { selector: "text=Copy", times: 1 }
    ]
  }
};

// =========================
// GENERATE KEY
// =========================
app.get('/generate', (req, res) => {
  const { days, maxUsage, unlimited, owner } = req.query;
  if (owner !== "angel") return res.json({status:"error", message:"Not authorized"});

  let keys = loadKeys();
  const newKey = "Angel_" + Math.random().toString(36).substring(2,10);

  keys[newKey] = {
    unlimited: unlimited === "true",
    usage: 0,
    maxUsage: parseInt(maxUsage)||10,
    expires: unlimited === "true" ? null : Date.now() + (parseInt(days)||1)*86400000
  };

  saveKeys(keys);
  res.json({status:"success", key:newKey});
});

// =========================
// REVOKE KEY
// =========================
app.get('/revoke', (req,res)=>{
  const { key, owner } = req.query;
  if(owner !== "angel") return res.json({status:"error", message:"Not authorized"});
  let keys = loadKeys();
  delete keys[key];
  saveKeys(keys);
  res.json({status:"success", message:"Key revoked"});
});

// =========================
// BYPASS API
// =========================
app.get('/bypass', async (req, res) => {
  const startTime = Date.now();
  const { url, apikey } = req.query;
  if(!url || !apikey) return res.json({status:"error", message:"Missing parameters"});

  let keys = loadKeys();
  const keyData = keys[apikey];
  if(!keyData) return res.json({status:"error", message:"Your key has been suspended or expired"});

  // expire check
  if(!keyData.unlimited && keyData.expires && Date.now() > keyData.expires){
    delete keys[apikey]; saveKeys(keys);
    return res.json({status:"error", message:"Your key expired"});
  }

  // usage check
  if(!keyData.unlimited && keyData.maxUsage > 0 && keyData.usage >= keyData.maxUsage){
    delete keys[apikey]; saveKeys(keys);
    return res.json({status:"error", message:"Usage limit reached"});
  }

  try {
    const hostname = new URL(url).hostname;
    const flow = flows[hostname];
    if(!flow) return res.json({status:"error", message:"No flow for this website"});

    const browser = await chromium.launch({headless:true});
    const context = await browser.newContext();
    const page = await context.newPage();

    context.on('page', async newPage => { await newPage.close(); });

    await page.goto(url,{waitUntil:"load"});
    await page.waitForTimeout(3000);

    for(const step of flow.steps){
      await clickMultiple(page, step.selector, step.times||1, step.waitAfter||2000);
      await protectFromAds(page, hostname);
    }

    // get copied result
    let copiedValue = "";
    try { copiedValue = await page.evaluate(()=> navigator.clipboard.readText()); }catch{}
    if(!copiedValue){
      try{ copiedValue = await page.$eval('input[type="text"]', el=> el.value);}catch{}
    }

    await browser.close();

    if(!keyData.unlimited){ keyData.usage++; saveKeys(keys); }

    res.json({
      status:"success",
      action:"bypass-url",
      result: copiedValue||"Nothing copied",
      made_by:"angel.l0l",
      website:hostname,
      time_taken: ((Date.now()-startTime)/1000).toFixed(2)+"s"
    });

  }catch(err){
    res.json({status:"error", message:"Bypass failed"});
  }
});

app.listen(PORT,()=>console.log("Server running on port "+PORT));