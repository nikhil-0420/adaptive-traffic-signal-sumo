/**
 * manifestInfo.js - Dynamic Experiment Manifest Utilities
 *
 * Provides dynamic experiment metadata formatting for UI footer and telemetry displays.
 * Strictly avoids hardcoded policy numbers or claims.
 */

/**
 * Format manifest data into a clean descriptive summary string.
 * Returns "Final results pending" if manifest is unavailable or incomplete.
 */
export function formatExperimentFooter(manifest) {
  if (!manifest) {
    return 'Final results pending';
  }

  const mainPolicies = manifest.main_matrix?.policies || manifest.policies || [];
  const ablationVariants = manifest.ablation_submatrix?.variants || manifest.ablation_variants || manifest.ablations || [];
  const conditions = manifest.main_matrix?.conditions || manifest.conditions || manifest.scenarios || [];
  const seeds = manifest.main_matrix?.seeds || manifest.seeds || [];

  const mainCount = Array.isArray(mainPolicies) ? mainPolicies.length : 0;
  const ablCount = Array.isArray(ablationVariants) ? ablationVariants.length : 0;
  const condCount = Array.isArray(conditions) ? conditions.length : 0;

  if (mainCount === 0 || condCount === 0) {
    return 'Final results pending';
  }

  let policyStr = `${mainCount} policies`;
  if (ablCount > 0) {
    policyStr += ` + ${ablCount} ablation`;
  }

  let seedStr = '';
  if (Array.isArray(seeds) && seeds.length > 0) {
    const minSeed = Math.min(...seeds);
    const maxSeed = Math.max(...seeds);
    seedStr = `, seeds ${minSeed}-${maxSeed}`;
  }

  return `${policyStr}, ${condCount} conditions${seedStr}`;
}

/**
 * Attempt to load the final experiment manifest.
 * Safely fails over without throwing.
 */
export async function loadFinalManifest() {
  const candidateUrls = [
    '/results/research/exp_marathahalli_improve_final/manifest.json',
    '/demo-data/manifest.json',
  ];

  for (const url of candidateUrls) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && (data.main_matrix || data.policies)) {
          return data;
        }
      }
    } catch {
      // Fall through to next candidate
    }
  }

  return null;
}
