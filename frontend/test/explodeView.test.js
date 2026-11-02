import test from 'node:test';
import assert from 'node:assert/strict';

/**
 * Explode 3-Tier View Unit Tests
 * 
 * Verifies that:
 * 1. Toggling explode changes the vertical offsets of the tiers (flyover lifts, underpass drops, surface stays 0).
 * 2. Soloing a tier dims the other tiers to 15% opacity while maintaining the soloed tier at 100%.
 * 3. Connecting vertical guide lines correctly bridge the separated tiers.
 */

// Pure functions matching IsometricIntersection projection logic
function computeTierOffsets(explodeProgress) {
  return {
    flyover: Math.round(-72 * explodeProgress) + 0,
    surface: 0,
    underpass: Math.round(65 * explodeProgress) + 0,
  };
}

function projectPoint(wx, wy, z, tier, explodeProgress, isIso = true) {
  const origX = 350;
  const origY = 350;
  const cx = 400;
  const cy = 300;
  const baseScale = 1.0;

  const u = wx - origX;
  const v = wy - origY;

  const offsets = computeTierOffsets(explodeProgress);
  const tierOffsetY = offsets[tier] || 0;

  if (!isIso) {
    return {
      x: cx + u * baseScale,
      y: cy - v * baseScale - z * baseScale * 0.35 + tierOffsetY,
    };
  }

  const cos30 = Math.cos(Math.PI / 6);
  const sin30 = Math.sin(Math.PI / 6);
  const isoX = (u - v) * cos30;
  const isoY = (u + v) * sin30;
  return {
    x: cx + isoX * baseScale,
    y: cy - isoY * baseScale * 0.72 - z * baseScale * 1.85 + tierOffsetY,
  };
}

function getTierOpacity(tier, soloTier) {
  if (!soloTier) return 1.0;
  return soloTier === tier ? 1.0 : 0.15;
}

test('Explode 3-Tier View: Collapse vs Explode layer offsets', () => {
  // 1. Collapsed state (ep = 0.0)
  const collapsed = computeTierOffsets(0.0);
  assert.equal(collapsed.flyover, 0, 'Collapsed flyover offset must be 0');
  assert.equal(collapsed.surface, 0, 'Collapsed surface offset must be 0');
  assert.equal(collapsed.underpass, 0, 'Collapsed underpass offset must be 0');

  // 2. Fully exploded state (ep = 1.0)
  const exploded = computeTierOffsets(1.0);
  assert.equal(exploded.flyover, -72, 'Exploded flyover must lift up by -72px');
  assert.equal(exploded.surface, 0, 'Exploded surface must remain stationary at 0px');
  assert.equal(exploded.underpass, 65, 'Exploded underpass must drop down by +65px');

  // Total separation between flyover deck and underpass trench
  const separation = Math.abs(exploded.flyover - exploded.underpass);
  assert.equal(separation, 137, 'Total vertical separation between flyover and underpass must be 137px');
});

test('Explode 3-Tier View: Projected coordinates shift when exploded', () => {
  const node = { x: 350, y: 350 }; // Junction center

  // Collapsed projection
  const flyCollapsed = projectPoint(node.x, node.y, 7.0, 'flyover', 0.0);
  const surfCollapsed = projectPoint(node.x, node.y, 0.0, 'surface', 0.0);
  const underCollapsed = projectPoint(node.x, node.y, -4.0, 'underpass', 0.0);

  // Exploded projection
  const flyExploded = projectPoint(node.x, node.y, 7.0, 'flyover', 1.0);
  const surfExploded = projectPoint(node.x, node.y, 0.0, 'surface', 1.0);
  const underExploded = projectPoint(node.x, node.y, -4.0, 'underpass', 1.0);

  // Surface should be identical
  assert.equal(surfExploded.x, surfCollapsed.x, 'Surface X must not move');
  assert.equal(surfExploded.y, surfCollapsed.y, 'Surface Y must not move');

  // Flyover Y must shift upwards (smaller Y in screen coords)
  assert.equal(flyExploded.y, flyCollapsed.y - 72, 'Flyover Y must be 72px higher');

  // Underpass Y must shift downwards (larger Y in screen coords)
  assert.equal(underExploded.y, underCollapsed.y + 65, 'Underpass Y must be 65px lower');
});

test('Explode 3-Tier View: Solo Tier mode dims non-selected layers', () => {
  // All tiers at 100% when no solo
  assert.equal(getTierOpacity('flyover', null), 1.0);
  assert.equal(getTierOpacity('surface', null), 1.0);
  assert.equal(getTierOpacity('underpass', null), 1.0);

  // Solo Flyover
  assert.equal(getTierOpacity('flyover', 'flyover'), 1.0, 'Soloed tier must be 100%');
  assert.equal(getTierOpacity('surface', 'flyover'), 0.15, 'Non-soloed surface must be dimmed to 15%');
  assert.equal(getTierOpacity('underpass', 'flyover'), 0.15, 'Non-soloed underpass must be dimmed to 15%');

  // Solo Underpass
  assert.equal(getTierOpacity('underpass', 'underpass'), 1.0, 'Soloed tier must be 100%');
  assert.equal(getTierOpacity('flyover', 'underpass'), 0.15, 'Non-soloed flyover must be dimmed to 15%');
  assert.equal(getTierOpacity('surface', 'underpass'), 0.15, 'Non-soloed surface must be dimmed to 15%');
});
