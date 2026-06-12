// Pure helpers for FlagForm.vue scope-target handling (TGT-01/TGT-02).
// Kept dependency-free (no Vue) so they're unit-testable without mounting.

export interface FlagTargetSelection {
  tenantId: string
  productId: string
  companyId: string
}

export interface FlagTargetFields {
  tenant_id: string | null
  product_id: string | null
  company_id: string | null
}

/**
 * Returns an error message when the active scope's target selection is
 * empty, or null when the selection is valid (global never requires a target).
 */
export function validateFlagTarget(scope: string, sel: FlagTargetSelection): string | null {
  switch (scope) {
    case 'product':
      return sel.productId ? null : 'Select a product for product-scoped flags'
    case 'tenant':
      return sel.tenantId ? null : 'Select a tenant for tenant-scoped flags'
    case 'company':
      return sel.companyId ? null : 'Select a company for company-scoped flags'
    default:
      return null
  }
}

/**
 * Builds the mutually-exclusive target fields for the FlagPayload: only the
 * active scope's id survives, the other two are explicitly null so the
 * backend clears stale columns on update.
 */
export function buildTargetFields(scope: string, sel: FlagTargetSelection): FlagTargetFields {
  return {
    tenant_id: scope === 'tenant' ? (sel.tenantId || null) : null,
    product_id: scope === 'product' ? (sel.productId || null) : null,
    company_id: scope === 'company' ? (sel.companyId || null) : null,
  }
}
