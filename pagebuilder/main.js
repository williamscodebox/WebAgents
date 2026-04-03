// -----------------------------
// PIXI SETUP
// -----------------------------
const app = new PIXI.Application({
  view: document.getElementById("phoenixCanvas"),
  resizeTo: window,
  transparent: true,
  backgroundAlpha: 0,   // <-- this is the key
  antialias: true
});

// -----------------------------
// TEXTURES
// -----------------------------
const emberTexture = PIXI.Texture.from("ember2.png");
const phoenixTexture = PIXI.Texture.from("phoenix.png");

// -----------------------------
// PHOENIX SPRITE
// -----------------------------
const phoenix = new PIXI.Sprite(phoenixTexture);
phoenix.anchor.set(0.5);
phoenix.scale.set(0.4); // adjust size as needed
phoenix.blendMode = PIXI.BLEND_MODES.ADD;
app.stage.addChild(phoenix);

// -----------------------------
// PHOENIX PATH
// -----------------------------
const path = document.getElementById("flightPath");
const length = path.getTotalLength();

// -----------------------------
// EMBER PARTICLE SPAWNER
// -----------------------------
//function spawnEmber(progress) {
//  const point = path.getPointAtLength(progress * length);
//
//  const sprite = new PIXI.Sprite(emberTexture);
//  sprite.anchor.set(0.5);
//  sprite.x = point.x;
//  sprite.y = point.y;
//
//  sprite.scale.set(0.15 + Math.random() * 0.25);
//  sprite.alpha = 0.7 + Math.random() * 0.3;
//
//  // Modern PixiJS tint
//  const r = 1;
//  const g = 0.4 + Math.random() * 0.4;
//  const b = 0;
//  sprite.tint = new PIXI.Color({ r, g, b }).toNumber();
//
//  sprite.blendMode = PIXI.BLEND_MODES.ADD;
//  app.stage.addChild(sprite);
//
//  // Ember drift + fade + destroy
//  gsap.to(sprite, {
//    duration: 1.2 + Math.random() * 0.6,
//    alpha: 0,
//    x: sprite.x + (Math.random() * 40 - 20),
//    y: sprite.y - (Math.random() * 40),
//    scale: 0,
//    ease: "power2.out",
//    onComplete: () => {
//      sprite.destroy({ children: true, texture: false, baseTexture: false });
//    }
//  });
//}

// -----------------------------
// HEAT DISTORTION FILTER
// -----------------------------
const displacementSprite = PIXI.Sprite.from("heat.png");
const displacementFilter = new PIXI.filters.DisplacementFilter(displacementSprite);

displacementSprite.texture.baseTexture.wrapMode = PIXI.WRAP_MODES.REPEAT;
displacementSprite.scale.set(2);// Make it invisible
displacementSprite.alpha = 0;

//app.stage.addChild(displacementSprite);

// Make it invisible
displacementSprite.alpha = 0;

// Make sure it never renders
displacementSprite.visible = false;
displacementSprite.renderable = false;

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
// PHOENIX FLIGHT ANIMATION (GSAP-SAFE)
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

const tailPoints = [];
for (let i = 0; i < 40; i++) {
  tailPoints.push(new PIXI.Point(400, -20));
}

const tail = new PIXI.SimpleRope(emberTexture, tailPoints);
tail.blendMode = PIXI.BLEND_MODES.ADD;

//const mask = new PIXI.Graphics()
//  .beginFill(0xffffff)
//  .drawCircle(0, 40, 400)
//  .endFill();
//
//tail.mask = mask;
//tail.addChild(mask);

tail.scale.set(0.8 + Math.random() * 0.3);
//tail.scale.set(0.5);   // thinner = less rectangular

tail.alpha = 0.4 + Math.random() * 0.3;


app.stage.addChild(tail);


function updatePhoenix(obj) {
  const progress = obj.p;

  // move the first point to phoenix position
tailPoints[0].x = phoenix.x;
tailPoints[0].y = phoenix.y;

// each point follows the previous one
for (let i = 1; i < tailPoints.length; i++) {
  const prev = tailPoints[i - 1];
  const p = tailPoints[i];

  p.x += (prev.x - p.x) * 0.40;
  p.y += (prev.y - p.y) * 0.40;
}


  // Position along the path
  const point = path.getPointAtLength(progress * length);
  phoenix.x = point.x;
  phoenix.y = point.y;


//
//  mask.x = phoenix.x;
//  mask.y = phoenix.y;


  // Rotation: face direction of travel
  const ahead = path.getPointAtLength((progress * length) + 1);
  phoenix.rotation = Math.atan2(ahead.y - point.y, ahead.x - point.x);
// subtle tail sway
//phoenix.rotation += Math.sin(progress * Math.PI * 4) * 0.1;



  // Ember trail
//  spawnEmber(progress);
}

console.log(app.renderer.background.alpha);
