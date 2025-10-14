⏺ Yes, you can use DataPackageSchema in a stateless way for forms. The current design already supports this:

  For rendering forms (stateless):
  - Use DataPackageSchema.field_definitions to get field specs
  - Use validation methods like validate_package_name(), validate_version(), validate_url()

  For building metadata from form data (stateless):
  Instead of the fluent builder API, create a static helper:

  @staticmethod
  def build_from_dict(form_data: Dict[str, Any]) -> Dict[str, Any]:
      """Build metadata from complete form data (stateless)."""
      builder = DataPackageBuilder()

      # Set basic info
      builder.set_basic_info(
          name=form_data['name'],
          title=form_data.get('title'),
          description=form_data.get('description'),
          version=form_data.get('version')
      )

      # Add other fields from form_data...

      return builder.build()

  Or use DataPackageSchema directly and build the dict manually without the builder, since the schema already has all validation and field definitions you need for UI rendering and validation.

  Would you like me to add a stateless helper method to the existing code?