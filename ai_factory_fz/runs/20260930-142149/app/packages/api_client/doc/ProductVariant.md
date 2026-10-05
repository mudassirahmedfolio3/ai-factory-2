# api_client.model.ProductVariant

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**sku** | **String** |  | 
**name** | **String** |  | 
**isDefault** | **bool** | Exactly one variant per product is the default. | 
**options** | [**BuiltList&lt;VariantOption&gt;**](VariantOption.md) |  | 
**price** | [**Money**](Money.md) |  | 
**salePrice** | [**Money**](Money.md) | Sale price actually charged when on sale; null when not on sale. Must be lower than price. | 
**stockQuantity** | **int** |  | 
**image** | [**Image**](Image.md) |  | 
**specificationOverrides** | [**LightingSpecifications**](LightingSpecifications.md) | Non-null fields replace the product specifications for this variant; null when the variant has no overrides. | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


