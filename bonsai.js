// ============================================
// DISCE METRICS (keine TypeScript Interfaces nötig)
// ============================================

// DisceMetrics Struktur als Kommentar zur Referenz:
// {
//   level_match, prosody_intelligibility, sentence_cohesion, task_exam_fit, goal_progress,
//   speaking_score, writing_score, listening_score, reading_score,
//   engagement_streak, session_completion_rate, consistency_score,
//   exam_ready, presentation_ready, interview_ready, authority_ready,
//   milestones_achieved, cefr_level,
//   cross_skill_correlation, readiness_velocity, weekly_delta
// }

// ============================================
// L-SYSTEM CLASSES
// ============================================

(function() {

const KeyboardKeysEnum = {
    P: 'KeyP',
    T: 'KeyT',
    W: 'KeyW',
};

class LSystemRule {
    constructor(source, target) {
        this.source = source;
        this.target = target;
    }

    isMatch(char) {
        return this.source === char;
    }

    apply() {
        return this.target;
    }
}

class LSystemDrawRule {
    constructor(source, applyFn) {
        this.source = source;
        this.apply = applyFn;
    }

    isMatch(char) {
        return this.source === char;
    }
}

class LSystem {
    constructor(data) {
        this.axiom = data.axiom;
        this.options = this.deepObjClone(data.options);
        this.rules = data.rules;
        this.drawRules = data.drawRules;
        this.states = [];
    }

    getNext(iterations = 1) {
        while (iterations > 0) {
            this.axiom = (this.axiom || '').split('')
            .map(char => {
                for (let i = 0; i < this.rules.length; i++) {
                    if (this.rules[i].isMatch(char)) {
                        return this.rules[i].apply();
                    }
                }
                return char;
            })
            .join('');
            iterations--;
        }
        return this.axiom;
    }

    drawRule(char, context) {
        const drawRule = this.drawRules.find(rule => rule.isMatch(char));
        if (drawRule) {
            drawRule.apply(context, this.options);
        }
    }

    saveState() {
        this.states.push(this.deepObjClone(this.options));
    }

    restoreState() {
        this.options = this.states.pop();
    }

    deepObjClone(object) {
        return JSON.parse(JSON.stringify(object));
    }
}

// ============================================
// DISCE METRICS MAPPER
// ============================================

class DisceTreeMapper {
  static metricsToOptions(metrics, baseOptions, treeType) {
  const newOptions = { ...baseOptions };
  
  // ============================================
  // 🛡️ NORMALISIERUNGSFUNKTION
  // ============================================
  const normalize = (value, max = 1) => {
    if (value === undefined || value === null) return 0.5;
    // Falls Wert > 1, vermutlich 0-100 Skala
    if (value > max) return Math.min(value / 100, 1);
    return Math.max(0, Math.min(1, value));
  };
  
  // ============================================
  // 📊 NORMALISIERTE METRIKEN (0-1 garantiert)
  // ============================================
  const m = {
    // Level: 1-4 (B1, B2, C1, C2)
    cefr_level: Math.max(1, Math.min(4, metrics.cefr_level || 2)),
    
    // Alle anderen Metriken: 0-1
    goal_progress: normalize(metrics.goal_progress),
    level_match: normalize(metrics.level_match),
    prosody_intelligibility: normalize(metrics.prosody_intelligibility),
    task_exam_fit: normalize(metrics.task_exam_fit),
    consistency_score: normalize(metrics.consistency_score),
    sentence_cohesion: normalize(metrics.sentence_cohesion), // ⚠️ KRITISCH!
    speaking_score: normalize(metrics.speaking_score),
    writing_score: normalize(metrics.writing_score),
    listening_score: normalize(metrics.listening_score),
    reading_score: normalize(metrics.reading_score),
    cross_skill_correlation: normalize(metrics.cross_skill_correlation),
    weekly_delta: normalize(metrics.weekly_delta),
    
    // Integer-Werte (ohne Normalisierung)
    engagement_streak: metrics.engagement_streak || 0,
    milestones_achieved: metrics.milestones_achieved || 0,
    
    // Readiness Flags (0 oder 1)
    exam_ready: metrics.exam_ready || 0,
    presentation_ready: metrics.presentation_ready || 0,
    interview_ready: metrics.interview_ready || 0,
    authority_ready: metrics.authority_ready || 0
  };
  
  // ============================================
  // 🌳 CORE STRUCTURE (ERHÖHTE BASISWERTE)
  // ============================================

   // Iterations: 6-12 statt 3-12
    const baseIterations = 6 + Math.floor(m.goal_progress * 6);
    const streakBonus = Math.min(2, Math.floor(m.engagement_streak / 20));
    newOptions.iterations = Math.min(baseIterations + streakBonus, 12);

    // Base Length: 60-140 statt 40-120
const baseLength = 60 + (m.level_match * 60) + (m.prosody_intelligibility * 40);
const cappedLength = Math.min(baseLength, 140);

// Baumgröße an Canvas-Breite anpassen (kleiner auf schmalen Displays)
newOptions.length = cappedLength * treeSizeFactor;

// Base Width: 4-14 statt 3-12
const baseWidth = 4 + (m.task_exam_fit * 7) + (m.consistency_score * 4);
const cappedWidth = Math.min(baseWidth, 14);

// Dicke leicht mit skalieren, aber nicht komplett ausdünnen
newOptions.width = cappedWidth * treeSizeFactor;


    // ============================================
    // 🌿 VERZWEIGUNGSTIEFE & DICHTE (NEU)
    // ============================================

    // Max Depth: 7-9 Ebenen (vorher undefiniert)
    const baseDepth = 7;
    const progressBonus = Math.floor(m.goal_progress * 2); // +0-2 bei Fortschritt
    newOptions.maxDepth = Math.min(baseDepth + progressBonus, 9);

    // Äste pro Ebene: 3-4 (mehr innere Struktur)
    newOptions.branchesPerLevel = 3 + Math.floor(m.sentence_cohesion * 1); // 3-4 Äste
  
// ============================================
// 🔀 BRANCHING BEHAVIOR
// ============================================

// ✅ NEUE VERSION: Realistische Bonsai-Winkel
// Winkel von der VERTIKALEN (nicht horizontal!)
// Max 35° = Äste wachsen noch deutlich nach oben

const minAngle = 10 + Math.floor(m.level_match * 5);  // 10-15°
const maxAngle = 20 + Math.floor(m.level_match * 8) + Math.floor(m.goal_progress * 7); // 20-35°

newOptions.angleRange = {
  min: Math.min(minAngle, 15),   // ✅ Nie weniger als 10°, nie mehr als 15°
  max: Math.min(maxAngle, 35)    // ✅ Nie mehr als 35° (statt 55°!)
};

// ✅ NEU: Aufwärts-Bias hinzufügen
// Verhindert symmetrisches Nach-unten-Wachsen
newOptions.upwardBias = 0.3 + (m.prosody_intelligibility * 0.2); // 0.3-0.5

// ✅ Schnellere Verkürzung = kompaktere Krone
newOptions.lengthDecreaseRatio = 0.68 + (m.prosody_intelligibility * 0.14); // 0.68-0.82

// ✅ Weniger wilde Asymmetrie
newOptions.widthDecreaseRatio = 0.82 + (m.sentence_cohesion * 0.11);

// ============================================
// 🎨 VARIATION & BALANCE
// ============================================

const skillBalance = (m.speaking_score + m.writing_score + 
                      m.listening_score + m.reading_score) / 4;
const skillDeviation = Math.abs(skillBalance - m.speaking_score) + 
                       Math.abs(skillBalance - m.writing_score);

newOptions.lengthRandomness = 0.05 + (skillDeviation * 0.25); // ✅ Weniger Chaos (0.35 → 0.25)
newOptions.angleAsymmetry = 0.05 + ((1 - m.cross_skill_correlation) * 0.15); // ✅ Deutlich reduziert (0.35 → 0.15)

// ✅ NEU: Gravitationseffekt (Äste hängen leicht)
newOptions.gravitationalPull = 0.05 + (m.milestones_achieved * 0.02); // Leichtes Durchhängen

  // ============================================
  // 🎨 COLOR MAPPING
  // ============================================
  
  const cefrColors = this.getCEFRColor(m.cefr_level, m.speaking_score);
  newOptions.colorR = cefrColors.r;
  newOptions.colorG = cefrColors.g;
  newOptions.colorB = cefrColors.b;
  newOptions.color = cefrColors.g;
  newOptions.colorDecreaseRatio = 1.08 + (m.weekly_delta * 0.04);
  
  // ============================================
  // ✨ VISUAL ENHANCEMENTS
  // ============================================
  
  newOptions.readinessSignals = {
    exam: m.exam_ready,
    presentation: m.presentation_ready,
    interview: m.interview_ready,
    authority: m.authority_ready
  };
  
  newOptions.milestones = m.milestones_achieved;
  newOptions.currentMetrics = m; // ✅ Normalisierte Metriken weitergeben!
  newOptions.depth = 0;
  
  return newOptions;
}
  
  static getCEFRColor(level, proficiency) {
    switch(level) {
      case 1: // B1: Brown tones
        return {
          r: 80 + Math.floor(proficiency * 20),
          g: 60 + Math.floor(proficiency * 40),
          b: 30 + Math.floor(proficiency * 20)
        };
      
      case 2: // B2: Dark Green
        return {
          r: 40 + Math.floor(proficiency * 30),
          g: 90 + Math.floor(proficiency * 50),
          b: 30 + Math.floor(proficiency * 30)
        };
      
      case 3: // C1: Vibrant Green
        return {
          r: 30 + Math.floor(proficiency * 30),
          g: 120 + Math.floor(proficiency * 60),
          b: 40 + Math.floor(proficiency * 40)
        };
      
      case 4: // C2: Bright/Lime Green
        return {
          r: 60 + Math.floor(proficiency * 40),
          g: 160 + Math.floor(proficiency * 60),
          b: 50 + Math.floor(proficiency * 50)
        };
      
      default:
        return { r: 50, g: 100, b: 40 };
    }
  }
  
  static selectRuleSet(metrics) {
    return 'tree';
  }
}

// ============================================
// HELPER FUNCTIONS
// ============================================

function degreeToRadian(degree) {
  return degree * Math.PI / 180;
}

function rangeInteger(min, max) {
  return min + Math.floor(Math.random() * (max - min));
}

function drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius) {
  let rot = Math.PI / 2 * 3;
  let x = cx;
  let y = cy;
  const step = Math.PI / spikes;

  ctx.beginPath();
  ctx.moveTo(cx, cy - outerRadius);
  
  for (let i = 0; i < spikes; i++) {
    x = cx + Math.cos(rot) * outerRadius;
    y = cy + Math.sin(rot) * outerRadius;
    ctx.lineTo(x, y);
    rot += step;

    x = cx + Math.cos(rot) * innerRadius;
    y = cy + Math.sin(rot) * innerRadius;
    ctx.lineTo(x, y);
    rot += step;
  }
  
  ctx.lineTo(cx, cy - outerRadius);
  ctx.closePath();
  ctx.fill();
}

// ============================================
// LEAF DRAWING FUNCTIONS
// ============================================

function drawSimpleLeaf(ctx, x, y, size, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(0, 0, size * 1.2, size * 1.8, Math.random() * Math.PI, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawRealisticLeaf(ctx, x, y, size, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(Math.random() * Math.PI * 2);
  
  ctx.fillStyle = color;
  
  // Größere Blattform
  const scale = 1.5; // Skalierungsfaktor
  
  ctx.beginPath();
  ctx.moveTo(0, -size * scale);
  ctx.bezierCurveTo(size * 0.5 * scale, -size * 0.7 * scale, size * 0.6 * scale, -size * 0.3 * scale, size * 0.3 * scale, 0);
  ctx.bezierCurveTo(size * 0.6 * scale, size * 0.3 * scale, size * 0.5 * scale, size * 0.7 * scale, 0, size * scale);
  ctx.bezierCurveTo(-size * 0.5 * scale, size * 0.7 * scale, -size * 0.6 * scale, size * 0.3 * scale, -size * 0.3 * scale, 0);
  ctx.bezierCurveTo(-size * 0.6 * scale, -size * 0.3 * scale, -size * 0.5 * scale, -size * 0.7 * scale, 0, -size * scale);
  ctx.fill();
  
  // Blattader (Mittelrippe)
  ctx.strokeStyle = 'rgba(0, 50, 0, 0.3)';
  ctx.lineWidth = 0.5;
  ctx.beginPath();
  ctx.moveTo(0, -size);
  ctx.lineTo(0, size);
  ctx.stroke();
  
  ctx.restore();
}

function drawClusterLeaves(ctx, x, y, size, color, count = 3) {
  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 / count) * i + Math.random() * 0.5;
    const radius = size * 0.5;
    const leafX = x + Math.cos(angle) * radius;
    const leafY = y + Math.sin(angle) * radius;
    drawSimpleLeaf(ctx, leafX, leafY, size * 0.6, color);
  }
}

function getLeafColor(metrics, depth) {
  const baseColors = DisceTreeMapper.getCEFRColor(metrics.cefr_level, metrics.speaking_score);
  
  // Hellere Farbe für Blätter
  const r = Math.min(255, baseColors.r + 30);
  const g = Math.min(255, baseColors.g + 40);
  const b = Math.min(255, baseColors.b + 20);
  
  // Tiefere Äste = dunklere Blätter
  const depthFactor = Math.max(0.6, 1 - (depth * 0.05));
  
  return `rgba(${Math.floor(r * depthFactor)}, ${Math.floor(g * depthFactor)}, ${Math.floor(b * depthFactor)}, 0.85)`;
}
  
  // ============================================
// 🌈 NEU: FARBVARIATION FÜR 3D-TIEFE
// ============================================
function adjustLeafColorForDepth(baseColor, depthRatio, randomFactor) {
  // baseColor = 'rgba(R, G, B, A)' String parsen
  const match = baseColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
  if (!match) return baseColor;
  
  let r = parseInt(match[1]);
  let g = parseInt(match[2]);
  let b = parseInt(match[3]);
  
  // ✅ Tiefere (innere) Blätter = dunkler
  const darkenFactor = 1 - (depthRatio * 0.3); // -0% außen, -30% innen
  r = Math.floor(r * darkenFactor);
  g = Math.floor(g * darkenFactor);
  b = Math.floor(b * darkenFactor);
  
  // ✅ Leichte zufällige Variation (Realismus)
  const variation = (randomFactor - 0.5) * 15; // ±7.5
  r = Math.max(0, Math.min(255, r + variation));
  g = Math.max(0, Math.min(255, g + variation));
  b = Math.max(0, Math.min(255, b + variation));
  
  // ✅ Opacity: Innere leicht transparenter
  const opacity = 0.7 + ((1 - depthRatio) * 0.3); // 0.7 innen, 1.0 außen
  
  return `rgba(${Math.floor(r)}, ${Math.floor(g)}, ${Math.floor(b)}, ${opacity.toFixed(2)})`;
}

// ============================================
// CANVAS SETUP - RESPONSIVE
// ============================================

const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');

const canvasContainer = canvas.parentElement;
const containerWidth = canvasContainer.clientWidth - 50; // 50px für Padding
const width = Math.min(containerWidth, 1200);            // Maximalbreite begrenzen
const height = Math.min(width * 0.6, 700);               // Etwas kompaktere Höhe

canvas.width = width;
canvas.height = height;

// Referenzbreite, auf die der Baum „kalibriert“ ist
const BASE_WIDTH = 1000;

// Größe des Baums relativ zur Breite (0 < factor ≤ 1)
const treeSizeFactor = Math.min(1, width / BASE_WIDTH);

const groundCenterPoint = {
  x: width / 2,
  y: height * 0.98, // leicht über dem unteren Rand
};



// ============================================
// L-SYSTEM DATA PRESETS
// ============================================

const pifagorLSystemData = {
    axiom: '0',
    options: {
        length: 5,
        iterations: 6,
        angle: degreeToRadian(45),
    },
    rules: [
        new LSystemRule('1', '11'),
        new LSystemRule('0', '1[0]0'),
    ],
    drawRules: [
        new LSystemDrawRule('0', (context, options) => {
            context.beginPath();
            context.moveTo(0, 0);
            context.lineTo(0, options.length);
            context.stroke();
        }),
        new LSystemDrawRule('1', (context, options) => {
            context.beginPath();
            context.moveTo(0, 0);
            context.lineTo(0, options.length);
            context.stroke();
            context.translate(0, options.length);
        }),
        new LSystemDrawRule('[', (context, options) => {
            context.save();
            context.rotate(-options.angle);
        }),
        new LSystemDrawRule(']', (context, options) => {
            context.restore();
            context.rotate(options.angle);
        }),
    ],
};

const weedLSystemData = {
    axiom: 'X',
    options: {
        length: 2.5,
        iterations: 6,
        angleRange: {
            min: 20,
            max: 30,
        },
    },
    rules: [
        new LSystemRule('X', 'F-[[X]+X]+F[+FX]-X'),
        new LSystemRule('F', 'FF'),
    ],
    drawRules: [
        new LSystemDrawRule('F', (context, options) => {
            context.beginPath();
            context.moveTo(0, 0);
            context.lineTo(0, options.length);
            context.stroke();
            context.translate(0, options.length);
        }),
        new LSystemDrawRule('+', (context, options) => {
            const angle = rangeInteger(options.angleRange.min, options.angleRange.max);
            context.rotate(degreeToRadian(angle));
        }),
        new LSystemDrawRule('-', (context, options) => {
            const angle = rangeInteger(options.angleRange.min, options.angleRange.max);
            context.rotate(-degreeToRadian(angle));
        }),
        new LSystemDrawRule('[', (context) => {
            context.save();
        }),
        new LSystemDrawRule(']', (context) => {
            context.restore();
        }),
    ],
};

const treeLSystemData = {
    axiom: 'X',
    options: {
        iterations: 12,
        length: 70,
        lengthDecreaseRatio: 0.79,
        width: 8,
        widthDecreaseRatio: 0.87,
        color: 51,
        colorR: 40,
        colorG: 100,
        colorB: 30,
        colorDecreaseRatio: 1.12,
        angleRange: {
            min: 5,
            max: 45,
        },
        lengthRandomness: 0.15,
        angleAsymmetry: 0.3,
        readinessSignals: {},
        milestones: 0,
    },
    rules: [
        new LSystemRule('X', 'F[@[-X]+X]'),
    ],
    drawRules: [
        new LSystemDrawRule('X', (context, options) => {
    // Ast zeichnen
    const r = Math.min(255, Math.floor(options.colorR || 40));
    const g = Math.min(255, Math.floor(options.colorG || options.color || 100));
    const b = Math.min(255, Math.floor(options.colorB || 30));
    context.strokeStyle = `rgb(${r}, ${g}, ${b})`;
    context.lineWidth = options.width;
    context.beginPath();
    context.moveTo(0, 0);
    context.lineTo(0, options.length);
    context.stroke();
    
    // ===== 🌿 NEUE VERSION: VOLLE KRONE =====
    const metrics = options.currentMetrics || {cefr_level: 2, speaking_score: 0.7, goal_progress: 0.6};
    const astLength = options.length;
    const astDicke = options.width;
    const astTiefe = options.depth || 0;
    
    // 🎯 DYNAMISCHE DICHTE basierend auf:
    // - Fortschritt (mehr = voller)
    // - Ast-Dicke (dünne Äste = mehr Blätter)
    // - Tiefe im Baum (tiefere Äste = dichter)
    
    const baseDensity = astDicke < 2 ? 6 :      // Dünne Äste: 6 Segmente
                        astDicke < 4 ? 5 :      // Mittlere: 5 Segmente
                        astDicke < 7 ? 4 : 3;   // Dicke: 3-4 Segmente
    
    const progressBonus = Math.floor(metrics.goal_progress * 2); // +0-2 bei hohem Fortschritt
    const numSegments = baseDensity + progressBonus;
    
    // ✅ ENTLANG DES GESAMTEN ASTES Blätter platzieren
    for (let segmentIdx = 0; segmentIdx < numSegments; segmentIdx++) {
        // Position entlang des Astes (0.0 = Basis, 1.0 = Spitze)
        const t = (segmentIdx + 0.3 + Math.random() * 0.4) / numSegments; // Leichte Variation
        const leafY = astLength * t;
        
        // 📊 WAHRSCHEINLICHKEIT: Steigt zur Spitze hin
        const baseProbability = astDicke < 2 ? 0.95 :   // Dünne Äste: Fast immer
                               astDicke < 4 ? 0.75 :   // Mittlere: 75%
                               astDicke < 7 ? 0.50 : 0.30; // Dicke: 30-50%
        
        const endBonus = t * 0.2;  // +20% zur Spitze hin
        const progressBonus = metrics.goal_progress * 0.15;
        const leafProbability = Math.min(0.98, baseProbability + endBonus + progressBonus);
        
        if (Math.random() < leafProbability) {
            // 📏 GRÖßE: Größer bei Fortschritt & höherem Level
            const baseSize = Math.max(3, astDicke * 1.4);
            const progressScale = 1 + (metrics.goal_progress * 0.5);
            const cefrScale = 0.7 + (metrics.cefr_level * 0.25);
            const leafSize = baseSize * progressScale * cefrScale * (0.8 + Math.random() * 0.4);
            
            // 🍃 ANZAHL der Blätter pro Segment: Mehr bei dünnen Ästen
            let numLeaves;
            if (astDicke < 2) {
                numLeaves = 2 + Math.floor(Math.random() * 2); // 2-3 Blätter
            } else if (astDicke < 4) {
                numLeaves = 1 + Math.floor(Math.random() * 2); // 1-2 Blätter
            } else {
                numLeaves = Math.random() < 0.6 ? 1 : 2; // Meist 1, manchmal 2
            }
            
            // Zusatz-Blätter für hohe Metriken
            if (metrics.cefr_level >= 3 && metrics.goal_progress > 0.7) {
                numLeaves += Math.floor(Math.random() * 2); // +0-1 Extra
            }
            
            for (let i = 0; i < numLeaves; i++) {
                // 🌈 FARBE mit Tiefenvariation
                const baseLeafColor = getLeafColor(metrics, astTiefe);
                const depthRatio = astTiefe / 10; // 0.0 außen, 1.0 innen
                const leafColor = adjustLeafColorForDepth(baseLeafColor, depthRatio, Math.random());
                
                // ✅ SEITLICHER OFFSET: Blätter wachsen vom Ast weg
                const spreadFactor = 1.5 + (t * 0.5); // Weiter außen = mehr Streuung
                const lateralOffset = (Math.random() - 0.5) * leafSize * spreadFactor;
                
                // ✅ LEICHTE VERTIKALE VARIATION
                const verticalJitter = (Math.random() - 0.5) * leafSize * 0.3;
                const finalY = leafY + verticalJitter;
                
                const cefrLevel = metrics.cefr_level;
                
                // 🎨 BLATTTYP basierend auf CEFR Level
                if (cefrLevel <= 1) {
                    drawSimpleLeaf(context, lateralOffset, finalY, leafSize, leafColor);
                } else if (cefrLevel === 2) {
                    if (Math.random() < 0.6) {
                        drawRealisticLeaf(context, lateralOffset, finalY, leafSize * 0.9, leafColor);
                    } else {
                        drawSimpleLeaf(context, lateralOffset, finalY, leafSize, leafColor);
                    }
                } else {
                    // C1/C2: Mix aus realistischen & Cluster-Blättern
                    if (Math.random() < 0.5) {
                        drawRealisticLeaf(context, lateralOffset, finalY, leafSize * 0.85, leafColor);
                    } else {
                        drawClusterLeaves(context, lateralOffset, finalY, leafSize * 0.7, leafColor, 3);
                    }
                }
            }
        }
    }
           
            // Milestone Früchte
            if (options.milestones > 0 && Math.random() < (options.milestones * 0.08)) {
                context.save();
                context.fillStyle = '#e74c3c';
                context.beginPath();
                context.arc(0, options.length * 0.7, 3, 0, Math.PI * 2);
                context.fill();
                context.restore();
            }
            
            // Readiness Sterne
            const hasReadiness = options.readinessSignals && 
                (options.readinessSignals.exam || options.readinessSignals.presentation || 
                 options.readinessSignals.interview || options.readinessSignals.authority);
                 
            if (hasReadiness && Math.random() < 0.12) {
                context.save();
                context.fillStyle = '#f1c40f';
                context.translate(0, options.length * 0.5);
                drawStar(context, 0, 0, 5, 2.5, 1.5);
                context.restore();
            }
        }),
        
        new LSystemDrawRule('F', (context, options) => {
            const lengthVariation = 1 + (Math.random() - 0.5) * (options.lengthRandomness || 0);
            const actualLength = options.length * lengthVariation;
            
            const r = Math.min(255, Math.floor(options.colorR || 40));
            const g = Math.min(255, Math.floor(options.colorG || options.color || 100));
            const b = Math.min(255, Math.floor(options.colorB || 30));
            context.strokeStyle = `rgb(${r}, ${g}, ${b})`;
            context.lineWidth = options.width;
            context.beginPath();
            context.moveTo(0, 0);
            context.lineTo(0, actualLength);
            context.stroke();
            context.translate(0, actualLength);
        }),
        
        new LSystemDrawRule('+', (context, options) => {
            const baseAngle = rangeInteger(options.angleRange.min, options.angleRange.max);
            const asymmetry = baseAngle * (options.angleAsymmetry || 0) * (Math.random() - 0.5);
            const radianAngle = degreeToRadian(baseAngle + asymmetry);
            context.rotate(radianAngle);
        }),
        
        new LSystemDrawRule('-', (context, options) => {
            const baseAngle = rangeInteger(options.angleRange.min, options.angleRange.max);
            const asymmetry = baseAngle * (options.angleAsymmetry || 0) * (Math.random() - 0.5);
            const radianAngle = degreeToRadian(baseAngle + asymmetry);
            context.rotate(-radianAngle);
        }),
        
        new LSystemDrawRule('[', (context) => {
            context.save();
            currentLSystem.saveState();
        }),
        
        new LSystemDrawRule(']', (context) => {
            context.restore();
            currentLSystem.restoreState();
        }),
        
        new LSystemDrawRule('@', (_, options) => {
            options.length *= options.lengthDecreaseRatio;
            options.width = Math.max(1, options.width * options.widthDecreaseRatio);
            
            if (options.colorR) options.colorR *= options.colorDecreaseRatio;
            if (options.colorG) options.colorG *= options.colorDecreaseRatio;
            if (options.colorB) options.colorB *= options.colorDecreaseRatio;
            options.color *= options.colorDecreaseRatio;
            
            if (options.depth !== undefined) {
                options.depth += 1;
            }
        }),
    ],
};

// ============================================
// KEYBOARD CONTROLS
// ============================================

const lSystemsMap = new Map([
    [KeyboardKeysEnum.P, pifagorLSystemData],
    [KeyboardKeysEnum.W, weedLSystemData],
    [KeyboardKeysEnum.T, treeLSystemData],
]);

let currentLSystem;
let lSystemText;

document.addEventListener('keypress', (event) => {
    if (lSystemsMap.has(event.code)) {
        setCurrentLSystem(lSystemsMap.get(event.code));
    }
});

setCurrentLSystem(treeLSystemData);

function setCurrentLSystem(lSystemData) {
    currentLSystem = new LSystem(lSystemData);
    update();
}

function update() {
    lSystemText = currentLSystem.getNext(currentLSystem.options.iterations);
    clear();
    drawAxiom(lSystemText);
}

function drawAxiom(axiom) {
  context.save();
  context.translate(groundCenterPoint.x, groundCenterPoint.y);
  context.rotate(Math.PI);

  (axiom || '').split('')
    .forEach(char => currentLSystem.drawRule(char, context));

  context.restore();
}



function clear() {
    context.fillStyle = '#fff';
    context.fillRect(0, 0, width, height);
}

function setContentText(text) {
    textElement.innerText = text;
}

// ============================================
// DISCE INTEGRATION
// ============================================

// Get slider elements - CORE METRICS
const levelMatchSlider = document.getElementById('level-match');
const prosodySlider = document.getElementById('prosody');
const cohesionSlider = document.getElementById('cohesion');
const taskFitSlider = document.getElementById('task-fit');
const goalProgressSlider = document.getElementById('goal-progress');
const cefrLevelSlider = document.getElementById('cefr-level');
const milestonesSlider = document.getElementById('milestones');
const streakSlider = document.getElementById('streak');

// Get slider elements - SKILL SCORES
const speakingScoreSlider = document.getElementById('speaking-score');
const writingScoreSlider = document.getElementById('writing-score');
const listeningScoreSlider = document.getElementById('listening-score');
const readingScoreSlider = document.getElementById('reading-score');

// Get slider elements - ADVANCED METRICS
const sessionCompletionSlider = document.getElementById('session-completion');
const consistencySlider = document.getElementById('consistency');
const crossSkillSlider = document.getElementById('cross-skill');
const readinessVelocitySlider = document.getElementById('readiness-velocity');
const weeklyDeltaSlider = document.getElementById('weekly-delta');

// Get value display elements - CORE METRICS
const levelMatchValue = document.getElementById('level-match-value');
const prosodyValue = document.getElementById('prosody-value');
const cohesionValue = document.getElementById('cohesion-value');
const taskFitValue = document.getElementById('task-fit-value');
const goalProgressValue = document.getElementById('goal-progress-value');
const cefrLevelValue = document.getElementById('cefr-level-value');
const milestonesValue = document.getElementById('milestones-value');
const streakValue = document.getElementById('streak-value');

const resetBtn = document.getElementById('reset-btn');
const generateDisceTreeBtn = document.getElementById('generate-disce-tree');
const exportJsonBtn = document.getElementById('export-json');
  
// Get value display elements - SKILL SCORES
const speakingScoreValue = document.getElementById('speaking-score-value');
const writingScoreValue = document.getElementById('writing-score-value');
const listeningScoreValue = document.getElementById('listening-score-value');
const readingScoreValue = document.getElementById('reading-score-value');

// Get value display elements - ADVANCED METRICS
const sessionCompletionValue = document.getElementById('session-completion-value');
const consistencyValue = document.getElementById('consistency-value');
const crossSkillValue = document.getElementById('cross-skill-value');
const readinessVelocityValue = document.getElementById('readiness-velocity-value');
const weeklyDeltaValue = document.getElementById('weekly-delta-value');

// Get checkbox elements
const examReadyCheck = document.getElementById('exam-ready');
const presentationReadyCheck = document.getElementById('presentation-ready');
const interviewReadyCheck = document.getElementById('interview-ready');
const authorityReadyCheck = document.getElementById('authority-ready');

const generateBtn = document.getElementById('generate-disce-tree');
const exportBtn = document.getElementById('export-json');

// Helper function to get current metrics - NOW ALL MANUAL
function getCurrentMetrics() {
  return {
    // Core metrics
    level_match: parseFloat(levelMatchSlider?.value || '0.7'),
    prosody_intelligibility: parseFloat(prosodySlider?.value || '0.75'),
    sentence_cohesion: parseFloat(cohesionSlider?.value || '0.65'),
    task_exam_fit: parseFloat(taskFitSlider?.value || '0.8'),
    goal_progress: parseFloat(goalProgressSlider?.value || '0.6'),
    
    // Skill scores - NOW MANUAL!
    speaking_score: parseFloat(speakingScoreSlider?.value || '0.72'),
    writing_score: parseFloat(writingScoreSlider?.value || '0.67'),
    listening_score: parseFloat(listeningScoreSlider?.value || '0.70'),
    reading_score: parseFloat(readingScoreSlider?.value || '0.74'),
    
    // Engagement
    engagement_streak: parseInt(streakSlider?.value || '15'),
    session_completion_rate: parseFloat(sessionCompletionSlider?.value || '0.76'),
    consistency_score: parseFloat(consistencySlider?.value || '0.88'),
    
    // Readiness
    exam_ready: examReadyCheck?.checked || false,
    presentation_ready: presentationReadyCheck?.checked || false,
    interview_ready: interviewReadyCheck?.checked || false,
    authority_ready: authorityReadyCheck?.checked || false,
    
    // Milestones & Level
    milestones_achieved: parseInt(milestonesSlider?.value || '3'),
    cefr_level: parseInt(cefrLevelSlider?.value || '2'),
    
    // Advanced metrics - NOW MANUAL!
    cross_skill_correlation: parseFloat(crossSkillSlider?.value || '0.89'),
    readiness_velocity: parseFloat(readinessVelocitySlider?.value || '0.40'),
    weekly_delta: parseFloat(weeklyDeltaSlider?.value || '0.04')
  };
}

// Auto-update when sliders change - CORE METRICS
const updateDisplay = (slider, display, suffix = '') => {
  slider?.addEventListener('input', (e) => {
    const value = e.target.value;
    if (display) display.textContent = value + suffix;
    generateDisceTree(getCurrentMetrics());
  });
};

  // Generate Disce Tree from metrics
function generateDisceTree(metrics) {
  const ruleSetName = DisceTreeMapper.selectRuleSet(metrics);
  const baseData = treeLSystemData; // Aktuell nur 'tree' unterstützt
  
  // Neue Options aus Metrics berechnen
  const newOptions = DisceTreeMapper.metricsToOptions(
    metrics, 
    baseData.options, 
    ruleSetName
  );
  
  // currentMetrics für Leaf-Drawing speichern
  newOptions.currentMetrics = metrics;
  newOptions.depth = 0;
  
  // L-System mit neuen Options erstellen
  const updatedData = {
    ...baseData,
    options: newOptions
  };
  
  setCurrentLSystem(updatedData);
  
  console.log('🌳 Tree generated:', {
  iterations: newOptions.iterations,
  length: newOptions.length.toFixed(1),
  width: newOptions.width.toFixed(1),
  angleRange: `${newOptions.angleRange.min}° - ${newOptions.angleRange.max}°`,
  cefrLevel: metrics.cefr_level,
  goalProgress: (metrics.goal_progress * 100).toFixed(0) + '%',
  lengthDecreaseRatio: newOptions.lengthDecreaseRatio.toFixed(3)
});
}
  
updateDisplay(levelMatchSlider, levelMatchValue);
updateDisplay(prosodySlider, prosodyValue);
updateDisplay(cohesionSlider, cohesionValue);
updateDisplay(taskFitSlider, taskFitValue);
updateDisplay(goalProgressSlider, goalProgressValue);

// CEFR Level special handling
cefrLevelSlider?.addEventListener('input', (e) => {
  const value = parseInt(e.target.value);
  const cefrLabel = ['', 'B1', 'B2', 'C1', 'C2'][value] || 'B2';
  if (cefrLevelValue) cefrLevelValue.textContent = `${value} (${cefrLabel})`;
  generateDisceTree(getCurrentMetrics());
});

updateDisplay(milestonesSlider, milestonesValue);
updateDisplay(streakSlider, streakValue, ' days');

// Auto-update when sliders change - SKILL SCORES
updateDisplay(speakingScoreSlider, speakingScoreValue);
updateDisplay(writingScoreSlider, writingScoreValue);
updateDisplay(listeningScoreSlider, listeningScoreValue);
updateDisplay(readingScoreSlider, readingScoreValue);

// Auto-update when sliders change - ADVANCED METRICS
updateDisplay(sessionCompletionSlider, sessionCompletionValue);
updateDisplay(consistencySlider, consistencyValue);
updateDisplay(crossSkillSlider, crossSkillValue);
updateDisplay(readinessVelocitySlider, readinessVelocityValue);
updateDisplay(weeklyDeltaSlider, weeklyDeltaValue);

// Checkbox listeners
[examReadyCheck, presentationReadyCheck, interviewReadyCheck, authorityReadyCheck].forEach(checkbox => {
  checkbox?.addEventListener('change', () => {
    generateDisceTree(getCurrentMetrics());
  });
});

// Button listeners
generateBtn?.addEventListener('click', () => {
  generateDisceTree(getCurrentMetrics());
});

exportBtn?.addEventListener('click', () => {
  const metrics = getCurrentMetrics();
  const ruleSetName = DisceTreeMapper.selectRuleSet(metrics);
  const baseOptions = treeLSystemData.options;
  
  const exportData = {
    metrics: metrics,
    timestamp: new Date().toISOString(),
    treeType: ruleSetName,
    options: DisceTreeMapper.metricsToOptions(metrics, baseOptions, ruleSetName)
  };
  
  console.log('Exported JSON:', JSON.stringify(exportData, null, 2));
  alert('JSON copied to console! (Press F12 to view)');
  
  if (navigator.clipboard) {
    navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
  }
});

// Generate initial tree on page load
generateDisceTree(getCurrentMetrics());


// ============================================
// RESET TO DEFAULTS
// ============================================

const DEFAULT_VALUES = {
  // Core metrics
  levelMatch: 0.7,
  prosody: 0.75,
  cohesion: 0.65,
  taskFit: 0.8,
  goalProgress: 0.6,
  cefrLevel: 2,
  milestones: 3,
  streak: 15,
  
  // Skill scores
  speakingScore: 0.72,
  writingScore: 0.67,
  listeningScore: 0.70,
  readingScore: 0.74,
  
  // Advanced metrics
  sessionCompletion: 0.76,
  consistency: 0.88,
  crossSkill: 0.89,
  readinessVelocity: 0.40,
  weeklyDelta: 0.04,
  
  // Checkboxes
  examReady: false,
  presentationReady: false,
  interviewReady: false,
  authorityReady: false
};

function resetToDefaults() {
  // Core metrics
  if (levelMatchSlider) {
    levelMatchSlider.value = DEFAULT_VALUES.levelMatch.toString();
    if (levelMatchValue) levelMatchValue.textContent = DEFAULT_VALUES.levelMatch.toString();
  }
  
  if (prosodySlider) {
    prosodySlider.value = DEFAULT_VALUES.prosody.toString();
    if (prosodyValue) prosodyValue.textContent = DEFAULT_VALUES.prosody.toString();
  }
  
  if (cohesionSlider) {
    cohesionSlider.value = DEFAULT_VALUES.cohesion.toString();
    if (cohesionValue) cohesionValue.textContent = DEFAULT_VALUES.cohesion.toString();
  }
  
  if (taskFitSlider) {
    taskFitSlider.value = DEFAULT_VALUES.taskFit.toString();
    if (taskFitValue) taskFitValue.textContent = DEFAULT_VALUES.taskFit.toString();
  }
  
  if (goalProgressSlider) {
    goalProgressSlider.value = DEFAULT_VALUES.goalProgress.toString();
    if (goalProgressValue) goalProgressValue.textContent = DEFAULT_VALUES.goalProgress.toString();
  }
  
  if (cefrLevelSlider) {
    cefrLevelSlider.value = DEFAULT_VALUES.cefrLevel.toString();
    const cefrLabel = ['', 'B1', 'B2', 'C1', 'C2'][DEFAULT_VALUES.cefrLevel];
    if (cefrLevelValue) cefrLevelValue.textContent = `${DEFAULT_VALUES.cefrLevel} (${cefrLabel})`;
  }
  
  if (milestonesSlider) {
    milestonesSlider.value = DEFAULT_VALUES.milestones.toString();
    if (milestonesValue) milestonesValue.textContent = DEFAULT_VALUES.milestones.toString();
  }
  
  if (streakSlider) {
    streakSlider.value = DEFAULT_VALUES.streak.toString();
    if (streakValue) streakValue.textContent = `${DEFAULT_VALUES.streak} days`;
  }
  
  // Skill scores
  if (speakingScoreSlider) {
    speakingScoreSlider.value = DEFAULT_VALUES.speakingScore.toString();
    if (speakingScoreValue) speakingScoreValue.textContent = DEFAULT_VALUES.speakingScore.toString();
  }
  
  if (writingScoreSlider) {
    writingScoreSlider.value = DEFAULT_VALUES.writingScore.toString();
    if (writingScoreValue) writingScoreValue.textContent = DEFAULT_VALUES.writingScore.toString();
  }
  
  if (listeningScoreSlider) {
    listeningScoreSlider.value = DEFAULT_VALUES.listeningScore.toString();
    if (listeningScoreValue) listeningScoreValue.textContent = DEFAULT_VALUES.listeningScore.toString();
  }
  
  if (readingScoreSlider) {
    readingScoreSlider.value = DEFAULT_VALUES.readingScore.toString();
    if (readingScoreValue) readingScoreValue.textContent = DEFAULT_VALUES.readingScore.toString();
  }
  
  // Advanced metrics
  if (sessionCompletionSlider) {
    sessionCompletionSlider.value = DEFAULT_VALUES.sessionCompletion.toString();
    if (sessionCompletionValue) sessionCompletionValue.textContent = DEFAULT_VALUES.sessionCompletion.toString();
  }
  
  if (consistencySlider) {
    consistencySlider.value = DEFAULT_VALUES.consistency.toString();
    if (consistencyValue) consistencyValue.textContent = DEFAULT_VALUES.consistency.toString();
  }
  
  if (crossSkillSlider) {
    crossSkillSlider.value = DEFAULT_VALUES.crossSkill.toString();
    if (crossSkillValue) crossSkillValue.textContent = DEFAULT_VALUES.crossSkill.toString();
  }
  
  if (readinessVelocitySlider) {
    readinessVelocitySlider.value = DEFAULT_VALUES.readinessVelocity.toString();
    if (readinessVelocityValue) readinessVelocityValue.textContent = DEFAULT_VALUES.readinessVelocity.toString();
  }
  
  if (weeklyDeltaSlider) {
    weeklyDeltaSlider.value = DEFAULT_VALUES.weeklyDelta.toString();
    if (weeklyDeltaValue) weeklyDeltaValue.textContent = DEFAULT_VALUES.weeklyDelta.toString();
  }
  
  // Checkboxes
  if (examReadyCheck) examReadyCheck.checked = DEFAULT_VALUES.examReady;
  if (presentationReadyCheck) presentationReadyCheck.checked = DEFAULT_VALUES.presentationReady;
  if (interviewReadyCheck) interviewReadyCheck.checked = DEFAULT_VALUES.interviewReady;
  if (authorityReadyCheck) authorityReadyCheck.checked = DEFAULT_VALUES.authorityReady;
  
  generateDisceTree(getCurrentMetrics());
  
  console.log('✅ Reset to default values');
}
if (resetBtn) {
  resetBtn.addEventListener('click', resetToDefaults);
}
  })();
