// -----------------------------
// PIXI SETUP
// -----------------------------
const app = new PIXI.Application({
  view: document.getElementById("phoenixCanvas"),
  resizeTo: window,
  transparent: true,
  antialias: true
});

// Ember texture
const emberTexture = PIXI.Texture.from("ember.png");

// -----------------------------
// PHOENIX PATH
// -----------------------------
const path = document.getElementById("flightPath");
const length = path.getTotalLength();

// -----------------------------
// EMBER PARTICLE SPAWNER
// -----------------------------
function spawnEmber(progress) {
  const point = path.getPointAtLength(progress * length);

  const sprite = new PIXI.Sprite(emberTexture);
  sprite.anchor.set(0.5);
  sprite.x = point.x;
  sprite.y = point.y;

  sprite.scale.set(0.15 + Math.random() * 0.25);
  sprite.alpha = 0.7 + Math.random() * 0.3;

  // Modern PixiJS tint
  const r = 1;
  const g = 0.4 + Math.random() * 0.4;
  const b = 0;
  sprite.tint = new PIXI.Color({ r, g, b }).toNumber();

  sprite.blendMode = PIXI.BLEND_MODES.ADD;
  app.stage.addChild(sprite);

  // Ember drift + fade + destroy
  gsap.to(sprite, {
    duration: 1.2 + Math.random() * 0.6,
    alpha: 0,
    x: sprite.x + (Math.random() * 40 - 20),
    y: sprite.y - (Math.random() * 40),
    scale: 0,
    ease: "power2.out",
    onComplete: () => {
      sprite.destroy({ children: true, texture: false, baseTexture: false });
    }
  });
}

// -----------------------------
// HEAT DISTORTION FILTER
// -----------------------------
const displacementSprite = PIXI.Sprite.from("heat.png");
const displacementFilter = new PIXI.filters.DisplacementFilter(displacementSprite);

displacementSprite.texture.baseTexture.wrapMode = PIXI.WRAP_MODES.REPEAT;
displacementSprite.scale.set(2);

app.stage.addChild(displacementSprite);
app.stage.filters = [displacementFilter];

// Animate heat shimmer
gsap.to(displacementSprite, {
  duration: 6,
  x: "+=200",
  y: "+=100",
  repeat: -1,
  ease: "none"
});

// -----------------------------
// PHOENIX CORE GLOW
// -----------------------------
//const core = new PIXI.Graphics();
//core.beginFill(0xffaa33);
//core.drawCircle(0, 0, 20);
//core.endFill();
//core.blendMode = PIXI.BLEND_MODES.ADD;
//app.stage.addChild(core);

// -----------------------------
// PHOENIX SPRITE
// -----------------------------
const phoenix = PIXI.Sprite.from("phoenix.png");
phoenix.anchor.set(0.5);
phoenix.scale.set(0.4); // adjust size as needed
phoenix.blendMode = PIXI.BLEND_MODES.ADD; // optional glow effect
app.stage.addChild(phoenix);

// -----------------------------
// WING-FLARE BURSTS
// -----------------------------
function wingFlare() {
  for (let i = 0; i < 20; i++) {
    spawnEmber(Math.random());
  }
}

gsap.timeline({ repeat: -1 })
  .call(wingFlare)
  .to({}, { duration: 0.8 })
  .call(wingFlare)
  .to({}, { duration: 1.2 });

// -----------------------------
// PHOENIX FLIGHT ANIMATION (GSAP-SAFE VERSION)
// -----------------------------
const flightObj = { p: 0 };

gsap.to(flightObj, {
  p: 1,
  duration: 5,
  repeat: -1,
  ease: "power2.inOut",
  onUpdate: updatePhoenix,
  onUpdateParams: [flightObj]
});

function updatePhoenix(obj) {
  const progress = obj.p;

  const point = path.getPointAtLength(progress * length);
//  core.x = point.x;
//  core.y = point.y;
  phoenix.x = point.x;
  phoenix.y = point.y;

  spawnEmber(progress);
}

console.log("Path length:", length);
